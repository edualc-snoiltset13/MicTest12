"""
Compute cryptographic checksums for one or more files.

Uses hashlib from the standard library and reads in fixed-size chunks so
files much larger than memory can be processed safely.

Usage:
    python hash_file.py <path> [<path> ...] [--algo sha256] [--check FILE]

Examples:
    python hash_file.py notes.txt
    python hash_file.py *.py --algo sha1
    python hash_file.py --check sums.txt
"""

import argparse
import hashlib
import sys

CHUNK_SIZE = 1024 * 1024  # 1 MiB


def hash_file(path, algo="sha256", chunk_size=CHUNK_SIZE):
    """Return the hex digest of the file at `path` using `algo`."""
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk_size), b""):
            h.update(block)
    return h.hexdigest()


def _print_sums(paths, algo):
    exit_code = 0
    for path in paths:
        try:
            print(f"{hash_file(path, algo)}  {path}")
        except (OSError, ValueError) as e:
            print(f"error: {path}: {e}", file=sys.stderr)
            exit_code = 1
    return exit_code


def _check_sums(checkfile, algo):
    """Verify entries of the form '<digest>  <path>' from `checkfile`."""
    exit_code = 0
    with open(checkfile, "r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                expected, path = line.split(None, 1)
            except ValueError:
                print(f"error: {checkfile}:{lineno}: malformed line", file=sys.stderr)
                exit_code = 1
                continue
            try:
                actual = hash_file(path, algo)
            except (OSError, ValueError) as e:
                print(f"{path}: FAILED ({e})")
                exit_code = 1
                continue
            if actual == expected:
                print(f"{path}: OK")
            else:
                print(f"{path}: FAILED")
                exit_code = 1
    return exit_code


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("paths", nargs="*", help="Files to hash")
    parser.add_argument("--algo", default="sha256",
                        help="hashlib algorithm name (default: sha256)")
    parser.add_argument("--check", metavar="FILE",
                        help="Verify digests listed in FILE instead of hashing")
    args = parser.parse_args(argv)

    if args.check:
        if args.paths:
            parser.error("--check does not take path arguments")
        return _check_sums(args.check, args.algo)

    if not args.paths:
        parser.error("provide at least one path, or use --check FILE")
    return _print_sums(args.paths, args.algo)


if __name__ == "__main__":
    sys.exit(main())
