"""
Scrape one or more web pages and run aggregate analysis on the results.

Complements web_scraper.py (per-URL extraction) by focusing on cross-page
analysis: combined keyword frequency, headline lengths, link-domain
distribution, HTML-table extraction with per-column numeric stats, and a
machine-readable JSON report ready for downstream analysis tools (pandas,
notebooks, BI dashboards).

Pure standard library — no third-party dependencies.

Usage:
    python scrape_analyze.py <url> [<url> ...] [options]
    python scrape_analyze.py --url-file urls.txt --output report.json
    python scrape_analyze.py <url> --tables-csv tables.csv

Options:
    --url-file PATH       Read URLs from a file (one per line, # for comments)
    --output PATH         Write JSON report to PATH (default: stdout)
    --tables-csv PATH     Also dump every scraped HTML table as one long CSV
    --top-words N         Top-N keywords in the global report (default: 25)
    --delay SECONDS       Delay between requests (default: 1.0)
    --timeout SECONDS     Per-request timeout (default: 15)
    --ignore-robots       Skip robots.txt check (only when authorized)
"""

import argparse
import csv
import json
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from collections import Counter, defaultdict
from html.parser import HTMLParser

USER_AGENT = "MicTest12-Analyzer/1.0 (+https://example.com)"
DEFAULT_TIMEOUT = 15
DEFAULT_DELAY = 1.0
DEFAULT_TOP_WORDS = 25

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "of", "in", "on", "at",
    "to", "for", "with", "by", "from", "as", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "should", "could", "may", "might", "can", "this",
    "that", "these", "those", "it", "its", "i", "you", "he", "she", "we",
    "they", "them", "their", "his", "her", "our", "your", "my", "me",
    "us", "him", "not", "no", "so", "than", "then", "there", "here",
    "what", "which", "who", "when", "where", "why", "how", "all", "any",
    "some", "more", "most", "other", "also", "just", "about", "into",
    "out", "up", "down", "over", "under", "again", "very", "too",
}

WORD_RE = re.compile(r"[a-z][a-z'\-]+")
NUMERIC_RE = re.compile(r"^-?\d{1,3}(,\d{3})*(\.\d+)?$|^-?\d+(\.\d+)?$")


class _PageParser(HTMLParser):
    """Extracts title, headings, paragraph text, links, and HTML tables."""

    SKIP_TAGS = {"script", "style", "noscript", "template"}
    HEADING_TAGS = {"h1", "h2", "h3"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = None
        self.headings = []  # list[(level, text)]
        self.paragraphs = []
        self.links = []  # list[href]
        self.tables = []  # list[list[list[str]]] — table -> rows -> cells

        self._buf = None
        self._buf_tag = None
        self._skip_depth = 0
        self._current_href = None

        # table state
        self._in_table = False
        self._current_table = None
        self._current_row = None
        self._cell_buf = None

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return

        attrs_d = dict(attrs)
        if tag == "title":
            self._buf, self._buf_tag = [], "title"
        elif tag in self.HEADING_TAGS:
            self._buf, self._buf_tag = [], tag
        elif tag == "p":
            self._buf, self._buf_tag = [], "p"
        elif tag == "a":
            href = attrs_d.get("href")
            if href:
                self.links.append(href)
                self._current_href = href
        elif tag == "table":
            self._in_table = True
            self._current_table = []
        elif tag == "tr" and self._in_table:
            self._current_row = []
        elif tag in ("td", "th") and self._current_row is not None:
            self._cell_buf = []

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS:
            if self._skip_depth:
                self._skip_depth -= 1
            return
        if self._skip_depth:
            return

        if self._buf_tag == tag and self._buf is not None:
            text = " ".join("".join(self._buf).split())
            if tag == "title" and text:
                self.title = text
            elif tag in self.HEADING_TAGS and text:
                self.headings.append((tag, text))
            elif tag == "p" and text:
                self.paragraphs.append(text)
            self._buf, self._buf_tag = None, None

        if tag == "a":
            self._current_href = None
        elif tag in ("td", "th") and self._cell_buf is not None:
            cell = " ".join("".join(self._cell_buf).split())
            self._current_row.append(cell)
            self._cell_buf = None
        elif tag == "tr" and self._current_row is not None:
            if self._current_row:
                self._current_table.append(self._current_row)
            self._current_row = None
        elif tag == "table" and self._in_table:
            if self._current_table:
                self.tables.append(self._current_table)
            self._current_table = None
            self._in_table = False

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._buf is not None:
            self._buf.append(data)
        if self._cell_buf is not None:
            self._cell_buf.append(data)


def is_allowed(url, ignore_robots=False):
    if ignore_robots:
        return True
    parsed = urllib.parse.urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except (urllib.error.URLError, OSError):
        return True
    return rp.can_fetch(USER_AGENT, url)


def fetch(url, timeout=DEFAULT_TIMEOUT):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        content_type = resp.headers.get_content_type() or ""
        charset = resp.headers.get_content_charset() or "utf-8"
        body = resp.read()
    try:
        text = body.decode(charset, errors="replace")
    except LookupError:
        text = body.decode("utf-8", errors="replace")
    return resp.status, content_type, text


def to_number(cell):
    s = cell.strip().replace(",", "")
    if not NUMERIC_RE.match(cell.strip()):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def analyze_table(rows):
    """Detect a header row + compute numeric stats per column."""
    if not rows:
        return None
    header = rows[0]
    data = rows[1:] if len(rows) > 1 else []
    width = max((len(r) for r in rows), default=0)
    columns = []
    for i in range(width):
        name = header[i] if i < len(header) else f"col_{i}"
        values = [r[i] if i < len(r) else "" for r in data]
        numeric = [v for v in (to_number(c) for c in values) if v is not None]
        col = {
            "name": name,
            "non_empty": sum(1 for v in values if v.strip()),
            "numeric_count": len(numeric),
        }
        if numeric:
            col["min"] = min(numeric)
            col["max"] = max(numeric)
            col["mean"] = round(statistics.fmean(numeric), 4)
            if len(numeric) > 1:
                col["stdev"] = round(statistics.stdev(numeric), 4)
        columns.append(col)
    return {
        "row_count": len(data),
        "column_count": width,
        "columns": columns,
    }


def scrape_page(url, ignore_robots=False, timeout=DEFAULT_TIMEOUT):
    rec = {"url": url, "ok": False}
    if not is_allowed(url, ignore_robots=ignore_robots):
        rec["error"] = "blocked by robots.txt"
        return rec
    try:
        status, ctype, html_text = fetch(url, timeout=timeout)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
        rec["error"] = f"fetch failed: {e}"
        return rec
    rec["status"] = status
    rec["content_type"] = ctype
    if "html" not in ctype:
        rec["error"] = f"not HTML ({ctype})"
        return rec

    parser = _PageParser()
    parser.feed(html_text)
    parser.close()

    body = " ".join(parser.paragraphs)
    words = WORD_RE.findall(body.lower())
    keywords = [w for w in words if w not in STOPWORDS and len(w) > 2]

    headline_lengths = [len(t.split()) for _, t in parser.headings]

    base_host = urllib.parse.urlparse(url).netloc
    link_domains = Counter()
    internal = external = 0
    for href in parser.links:
        if not href or href.startswith(("javascript:", "mailto:", "#")):
            continue
        absolute = urllib.parse.urljoin(url, href)
        host = urllib.parse.urlparse(absolute).netloc
        if not host:
            continue
        link_domains[host] += 1
        if host == base_host:
            internal += 1
        else:
            external += 1

    rec.update({
        "ok": True,
        "title": parser.title,
        "headings": [{"level": lvl, "text": txt} for lvl, txt in parser.headings],
        "headline_word_lengths": headline_lengths,
        "paragraph_count": len(parser.paragraphs),
        "word_count": len(words),
        "unique_word_count": len(set(words)),
        "keyword_freq": dict(Counter(keywords)),
        "links_internal": internal,
        "links_external": external,
        "link_domains": dict(link_domains),
        "tables": [analyze_table(t) for t in parser.tables],
        "_raw_tables": parser.tables,
    })
    return rec


def aggregate(records, top_words=DEFAULT_TOP_WORDS):
    ok = [r for r in records if r.get("ok")]
    failures = [{"url": r["url"], "error": r.get("error")} for r in records if not r.get("ok")]

    global_keywords = Counter()
    domain_totals = Counter()
    all_headline_lengths = []
    word_counts = []
    table_count = 0

    for r in ok:
        global_keywords.update(r["keyword_freq"])
        domain_totals.update(r["link_domains"])
        all_headline_lengths.extend(r["headline_word_lengths"])
        word_counts.append(r["word_count"])
        table_count += len(r["tables"])

    summary = {
        "pages_scraped": len(records),
        "pages_ok": len(ok),
        "pages_failed": len(failures),
        "total_tables": table_count,
        "total_words": sum(word_counts),
        "avg_words_per_page": round(statistics.fmean(word_counts), 2) if word_counts else 0,
        "median_words_per_page": statistics.median(word_counts) if word_counts else 0,
        "avg_headline_words": round(statistics.fmean(all_headline_lengths), 2) if all_headline_lengths else 0,
        "top_keywords": global_keywords.most_common(top_words),
        "top_link_domains": domain_totals.most_common(top_words),
        "failures": failures,
    }
    return summary


def write_tables_csv(records, path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["url", "table_index", "row_index", "cells"])
        for r in records:
            if not r.get("ok"):
                continue
            for ti, table in enumerate(r.get("_raw_tables", [])):
                for ri, row in enumerate(table):
                    w.writerow([r["url"], ti, ri, " | ".join(row)])


def load_urls(args):
    urls = list(args.urls)
    if args.url_file:
        with open(args.url_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)
    return urls


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Scrape multiple pages and produce an aggregate analysis report.",
    )
    parser.add_argument("urls", nargs="*", help="URLs to scrape")
    parser.add_argument("--url-file", help="File with one URL per line")
    parser.add_argument("--output", help="Write JSON report to this file")
    parser.add_argument("--tables-csv", help="Also dump all scraped tables to this CSV")
    parser.add_argument("--top-words", type=int, default=DEFAULT_TOP_WORDS)
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--ignore-robots", action="store_true")
    args = parser.parse_args(argv)

    urls = load_urls(args)
    if not urls:
        parser.error("provide at least one URL (positional or via --url-file)")

    records = []
    for i, url in enumerate(urls):
        if i > 0 and args.delay > 0:
            time.sleep(args.delay)
        print(f"[{i + 1}/{len(urls)}] {url}", file=sys.stderr)
        rec = scrape_page(url, ignore_robots=args.ignore_robots, timeout=args.timeout)
        if not rec.get("ok"):
            print(f"  ! {rec.get('error')}", file=sys.stderr)
        records.append(rec)

    if args.tables_csv:
        write_tables_csv(records, args.tables_csv)

    for r in records:
        r.pop("_raw_tables", None)

    report = {
        "summary": aggregate(records, top_words=args.top_words),
        "pages": records,
    }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            f.write("\n")
    else:
        json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")

    return 0 if report["summary"]["pages_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
