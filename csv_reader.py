"""
Simple CSV reader.

Reads a CSV file and prints its contents as a table.
Pure standard library.

Usage:
    python csv_reader.py data.csv
    python csv_reader.py data.csv --delimiter ";"
    python csv_reader.py data.csv --no-header
"""

import argparse
import csv
import sys


def read_csv(path, delimiter=",", has_header=True):
    """Read a CSV file.

    Returns a (header, rows) tuple. When has_header is False the header is
    an empty list and every line is returned as a data row.
    """
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=delimiter)
        rows = [row for row in reader]

    if has_header and rows:
        return rows[0], rows[1:]
    return [], rows


def read_csv_as_dicts(path, delimiter=","):
    """Read a CSV file with a header row into a list of dictionaries."""
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=delimiter))


def format_table(header, rows):
    """Format rows as an aligned plain-text table."""
    all_rows = ([header] + rows) if header else rows
    if not all_rows:
        return ""

    width = max(len(row) for row in all_rows)
    padded = [row + [""] * (width - len(row)) for row in all_rows]
    widths = [max(len(row[i]) for row in padded) for i in range(width)]

    def line(row):
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)).rstrip()

    lines = [line(row) for row in padded]
    if header:
        lines.insert(1, "  ".join("-" * w for w in widths))
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read and display a CSV file.")
    parser.add_argument("path", help="path to the CSV file")
    parser.add_argument(
        "-d", "--delimiter", default=",", help="field delimiter (default: ',')"
    )
    parser.add_argument(
        "--no-header",
        dest="has_header",
        action="store_false",
        help="treat the first line as data instead of a header",
    )
    args = parser.parse_args(argv)

    try:
        header, rows = read_csv(args.path, args.delimiter, args.has_header)
    except FileNotFoundError:
        print("error: file not found: {}".format(args.path), file=sys.stderr)
        return 1
    except OSError as exc:
        print("error: could not read {}: {}".format(args.path, exc), file=sys.stderr)
        return 1

    table = format_table(header, rows)
    if table:
        print(table)
    print("\n{} row(s)".format(len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
