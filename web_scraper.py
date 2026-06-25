"""
Web scraper for data analysis — pure standard library.

Fetches one or more URLs, parses their HTML, and emits an analysis-ready
record per URL (title, meta description, headings, link counts, paragraph
text, word frequencies). Respects robots.txt and rate-limits requests.

Usage:
    python web_scraper.py <url> [<url> ...] [--format json|csv]
                                            [--output FILE]
                                            [--delay SECONDS]
                                            [--top-words N]
                                            [--ignore-robots]

Examples:
    python web_scraper.py https://example.com
    python web_scraper.py https://a.com https://b.com --format csv --output data.csv
"""

import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from collections import Counter
from html.parser import HTMLParser

USER_AGENT = "MicTest12-Scraper/1.0 (+https://example.com)"
DEFAULT_TIMEOUT = 15
DEFAULT_DELAY = 1.0
DEFAULT_TOP_WORDS = 15

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


class _PageParser(HTMLParser):
    """Collects title, meta description, headings, links, and paragraph text."""

    SKIP_TAGS = {"script", "style", "noscript", "template"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = None
        self.description = None
        self.headings = {"h1": [], "h2": [], "h3": []}
        self.links = []  # list[(text, href)]
        self.paragraphs = []
        self._text_target = None
        self._current_link_text = []
        self._current_href = None
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return

        attrs_d = dict(attrs)
        if tag == "title":
            self._text_target = ("title", [])
        elif tag == "meta":
            name = (attrs_d.get("name") or attrs_d.get("property") or "").lower()
            if name in ("description", "og:description") and self.description is None:
                self.description = (attrs_d.get("content") or "").strip() or None
        elif tag in self.headings:
            self._text_target = (tag, [])
        elif tag == "p":
            self._text_target = ("p", [])
        elif tag == "a":
            self._current_href = attrs_d.get("href")
            self._current_link_text = []

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS:
            if self._skip_depth:
                self._skip_depth -= 1
            return
        if self._skip_depth:
            return

        if self._text_target and tag == self._text_target[0]:
            text = " ".join("".join(self._text_target[1]).split())
            if tag == "title" and text:
                self.title = text
            elif tag in self.headings and text:
                self.headings[tag].append(text)
            elif tag == "p" and text:
                self.paragraphs.append(text)
            self._text_target = None
        if tag == "a" and self._current_href is not None:
            text = " ".join("".join(self._current_link_text).split())
            self.links.append((text, self._current_href))
            self._current_href = None
            self._current_link_text = []

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._text_target:
            self._text_target[1].append(data)
        if self._current_href is not None:
            self._current_link_text.append(data)


def _is_allowed(url, ignore_robots=False):
    if ignore_robots:
        return True
    parsed = urllib.parse.urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except (urllib.error.URLError, OSError):
        return True  # No robots.txt available — proceed.
    return rp.can_fetch(USER_AGENT, url)


def fetch(url, timeout=DEFAULT_TIMEOUT):
    """Return (status, content_type, html_text) for a URL."""
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


def parse(html_text, base_url=None):
    p = _PageParser()
    p.feed(html_text)
    p.close()

    internal, external = 0, 0
    base_host = urllib.parse.urlparse(base_url).netloc if base_url else None
    normalized_links = []
    for text, href in p.links:
        if not href or href.startswith(("javascript:", "mailto:", "#")):
            continue
        absolute = urllib.parse.urljoin(base_url, href) if base_url else href
        host = urllib.parse.urlparse(absolute).netloc
        if base_host and host == base_host:
            internal += 1
        elif host:
            external += 1
        normalized_links.append({"text": text, "href": absolute})

    body_text = " ".join(p.paragraphs)
    words = WORD_RE.findall(body_text.lower())
    meaningful = [w for w in words if w not in STOPWORDS and len(w) > 2]
    word_freq = Counter(meaningful)

    return {
        "title": p.title,
        "description": p.description,
        "headings": p.headings,
        "links_total": len(normalized_links),
        "links_internal": internal,
        "links_external": external,
        "links": normalized_links,
        "paragraphs": p.paragraphs,
        "word_count": len(words),
        "unique_word_count": len(set(words)),
        "word_freq": word_freq,
    }


def scrape(url, ignore_robots=False, timeout=DEFAULT_TIMEOUT, top_words=DEFAULT_TOP_WORDS):
    """Fetch + parse a single URL. Returns an analysis record (dict)."""
    record = {"url": url, "ok": False}
    if not _is_allowed(url, ignore_robots=ignore_robots):
        record["error"] = "blocked by robots.txt"
        return record
    try:
        status, content_type, html_text = fetch(url, timeout=timeout)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
        record["error"] = f"fetch failed: {e}"
        return record
    record["status"] = status
    record["content_type"] = content_type
    if "html" not in content_type:
        record["error"] = f"not an HTML response ({content_type})"
        return record
    parsed = parse(html_text, base_url=url)
    parsed["top_words"] = parsed["word_freq"].most_common(top_words)
    parsed["word_freq"] = dict(parsed["word_freq"])
    record.update(parsed)
    record["ok"] = True
    return record


def _flat_csv_row(rec):
    return {
        "url": rec.get("url", ""),
        "ok": rec.get("ok", False),
        "status": rec.get("status", ""),
        "title": rec.get("title", "") or "",
        "description": rec.get("description", "") or "",
        "h1_count": len(rec.get("headings", {}).get("h1", [])),
        "h2_count": len(rec.get("headings", {}).get("h2", [])),
        "h3_count": len(rec.get("headings", {}).get("h3", [])),
        "links_total": rec.get("links_total", 0),
        "links_internal": rec.get("links_internal", 0),
        "links_external": rec.get("links_external", 0),
        "paragraph_count": len(rec.get("paragraphs", [])),
        "word_count": rec.get("word_count", 0),
        "unique_word_count": rec.get("unique_word_count", 0),
        "top_words": ", ".join(f"{w}:{n}" for w, n in rec.get("top_words", [])),
        "error": rec.get("error", ""),
    }


def write_output(records, fmt, path):
    stream = open(path, "w", encoding="utf-8", newline="") if path else sys.stdout
    try:
        if fmt == "json":
            json.dump(records, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        else:  # csv
            rows = [_flat_csv_row(r) for r in records]
            if not rows:
                return
            writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    finally:
        if path:
            stream.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("urls", nargs="+", help="One or more URLs to scrape")
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    parser.add_argument("--output", default=None, help="File to write (default: stdout)")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY,
                        help="Seconds to wait between requests")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--top-words", type=int, default=DEFAULT_TOP_WORDS)
    parser.add_argument("--ignore-robots", action="store_true",
                        help="Skip robots.txt check (use only when authorized)")
    args = parser.parse_args(argv)

    records = []
    for i, url in enumerate(args.urls):
        if i > 0 and args.delay > 0:
            time.sleep(args.delay)
        print(f"[{i + 1}/{len(args.urls)}] {url}", file=sys.stderr)
        rec = scrape(url, ignore_robots=args.ignore_robots,
                     timeout=args.timeout, top_words=args.top_words)
        if not rec["ok"]:
            print(f"  ! {rec.get('error')}", file=sys.stderr)
        records.append(rec)

    write_output(records, args.format, args.output)
    failures = sum(1 for r in records if not r["ok"])
    return 1 if failures and len(records) == failures else 0


if __name__ == "__main__":
    sys.exit(main())
