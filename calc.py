"""Compact CLI calculator: evaluate one expression and print the result.

    $ python calc.py "2 + 3 * (4 - 1)"
    11

Supports + - * / // % ** parentheses, and sqrt/abs functions. Pure stdlib.
"""

import sys

from calculator import _format, evaluate


def main(argv):
    if len(argv) < 2:
        print("usage: calc.py <expression>", file=sys.stderr)
        sys.exit(2)
    try:
        print(_format(evaluate(" ".join(argv[1:]))))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv)
