"""
Scrape HTML tables from web pages and produce analysis-ready output.

Complements web_scraper.py (which extracts page content/text) by pulling
structured tabular data and running quick numeric analysis on it.

Usage:
    python scrape_for_analysis.py <url> [<url> ...] [--output FILE]
                                                    [--format json|csv]
                                                    [--table-index N]
                                                    [--delay SECONDS]
                                                    [--no-analysis]

Examples:
    python scrape_for_analysis.py https://en.wikipedia.org/wiki/List_of_countries_by_GDP
    python scrape_for_analysis.py https://example.com --format csv --output out.csv
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
from html.parser import HTMLParser

USER_AGENT = "MicTest12-AnalysisScraper/1.0 (+https://example.com)"
DEFAULT_TIMEOUT = 15
DEFAULT_DELAY = 1.0

NUMERIC_RE = re.compile(r"^-?\d{1,3}(?:[,\s]\d{3})*(?:\.\d+)?$|^-?\d+(?:\.\d+)?$")


class _TableParser(HTMLParser):
    """Extracts <table> data as a list of tables, each a list of rows."""

    SKIP_TAGS = {"script", "style", "noscript"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self._table_stack = []
        self._row = None
        self._cell = None
        self._cell_is_header = False
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "table":
            self._table_stack.append({"headers": [], "rows": []})
        elif tag == "tr" and self._table_stack:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
            self._cell_is_header = (tag == "th")

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS:
            if self._skip_depth:
                self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag in ("td", "th") and self._cell is not None:
            text = " ".join("".join(self._cell).split())
            self._row.append({"text": text, "header": self._cell_is_header})
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table_stack:
            table = self._table_stack[-1]
            all_headers = self._row and all(c["header"] for c in self._row)
            values = [c["text"] for c in self._row]
            if all_headers and not table["rows"]:
                table["headers"] = values
            elif values:
                table["rows"].append(values)
            self._row = None
        elif tag == "table" and self._table_stack:
            table = self._table_stack.pop()
            if not table["headers"] and table["rows"]:
                first = table["rows"][0]
                table["headers"] = [f"col_{i + 1}" for i in range(len(first))]
            if table["rows"]:
                self.tables.append(table)

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._cell is not None:
            self._cell.append(data)


def _to_number(text):
    if not text:
        return None
    cleaned = text.replace(",", "").replace(" ", "").strip()
    if NUMERIC_RE.match(text.strip()):
        try:
            value = float(cleaned)
            return int(value) if value.is_integer() else value
        except ValueError:
            return None
    return None


def analyze_table(table):
    """Compute per-column summary stats (count, numeric stats, samples)."""
    headers = table["headers"]
    rows = table["rows"]
    summary = []
    for i, name in enumerate(headers):
        values = [row[i] if i < len(row) else "" for row in rows]
        numeric = [n for n in (_to_number(v) for v in values) if n is not None]
        non_empty = [v for v in values if v]
        col = {
            "column": name,
            "non_empty_count": len(non_empty),
            "unique_count": len(set(non_empty)),
            "numeric_count": len(numeric),
            "sample_values": non_empty[:3],
        }
        if numeric:
            col["min"] = min(numeric)
            col["max"] = max(numeric)
            col["sum"] = sum(numeric)
            col["mean"] = round(statistics.fmean(numeric), 4)
            if len(numeric) >= 2:
                col["stdev"] = round(statistics.stdev(numeric), 4)
                col["median"] = statistics.median(numeric)
        summary.append(col)
    return summary


def fetch(url, timeout=DEFAULT_TIMEOUT):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        content_type = resp.headers.get_content_type() or ""
        body = resp.read()
    try:
        text = body.decode(charset, errors="replace")
    except LookupError:
        text = body.decode("utf-8", errors="replace")
    return resp.status, content_type, text


def scrape_tables(url, timeout=DEFAULT_TIMEOUT, table_index=None, run_analysis=True):
    record = {"url": url, "ok": False, "tables": []}
    try:
        status, content_type, html_text = fetch(url, timeout=timeout)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
        record["error"] = f"fetch failed: {e}"
        return record
    record["status"] = status
    record["content_type"] = content_type
    if "html" not in content_type:
        record["error"] = f"not HTML ({content_type})"
        return record

    parser = _TableParser()
    parser.feed(html_text)
    parser.close()

    tables = parser.tables
    if table_index is not None:
        if 0 <= table_index < len(tables):
            tables = [tables[table_index]]
        else:
            record["error"] = f"table_index {table_index} out of range (found {len(tables)})"
            return record

    for i, t in enumerate(tables):
        entry = {
            "index": i,
            "headers": t["headers"],
            "row_count": len(t["rows"]),
            "column_count": len(t["headers"]),
            "rows": t["rows"],
        }
        if run_analysis:
            entry["analysis"] = analyze_table(t)
        record["tables"].append(entry)
    record["table_count"] = len(record["tables"])
    record["ok"] = True
    return record


def write_csv(records, path):
    stream = open(path, "w", encoding="utf-8", newline="") if path else sys.stdout
    try:
        writer = csv.writer(stream)
        for rec in records:
            for table in rec.get("tables", []):
                writer.writerow([f"# {rec['url']} table {table['index']}"])
                writer.writerow(table["headers"])
                writer.writerows(table["rows"])
                writer.writerow([])
    finally:
        if path:
            stream.close()


def write_json(records, path):
    stream = open(path, "w", encoding="utf-8") if path else sys.stdout
    try:
        json.dump(records, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    finally:
        if path:
            stream.close()


def print_summary(records, out=sys.stderr):
    for rec in records:
        if not rec["ok"]:
            print(f"[!] {rec['url']}: {rec.get('error')}", file=out)
            continue
        print(f"[✓] {rec['url']}: {rec['table_count']} table(s)", file=out)
        for table in rec["tables"]:
            print(f"    table {table['index']}: {table['row_count']} rows x "
                  f"{table['column_count']} cols", file=out)
            for col in table.get("analysis", []):
                bits = [f"non_empty={col['non_empty_count']}",
                        f"unique={col['unique_count']}"]
                if col.get("numeric_count"):
                    bits.append(f"mean={col.get('mean')}")
                    bits.append(f"min={col.get('min')}")
                    bits.append(f"max={col.get('max')}")
                print(f"      - {col['column']}: " + ", ".join(bits), file=out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("urls", nargs="+", help="One or more URLs to scrape")
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    parser.add_argument("--output", default=None,
                        help="File to write (default: stdout)")
    parser.add_argument("--table-index", type=int, default=None,
                        help="Only extract the Nth table (0-indexed)")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY,
                        help="Seconds between requests")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--no-analysis", action="store_true",
                        help="Skip per-column numeric analysis")
    args = parser.parse_args(argv)

    records = []
    for i, url in enumerate(args.urls):
        if i > 0 and args.delay > 0:
            time.sleep(args.delay)
        print(f"[{i + 1}/{len(args.urls)}] fetching {url}", file=sys.stderr)
        rec = scrape_tables(url, timeout=args.timeout,
                            table_index=args.table_index,
                            run_analysis=not args.no_analysis)
        records.append(rec)

    print_summary(records)
    if args.format == "csv":
        write_csv(records, args.output)
    else:
        write_json(records, args.output)

    failures = sum(1 for r in records if not r["ok"])
    return 1 if failures and failures == len(records) else 0


if __name__ == "__main__":
    sys.exit(main())
