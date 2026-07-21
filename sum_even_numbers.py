"""
Sum the even numbers in a list.

Pure standard library.

Usage:
    python sum_even_numbers.py 1 2 3 4 5 6   # prints 12
"""

import sys


def sum_even_numbers(numbers):
    """Return the sum of the even numbers in *numbers*.

    Accepts any iterable of ints and floats. Floats are included only
    when they are whole and even (e.g. 4.0 counts, 4.5 does not).

    Raises TypeError for any element that is not an int or float —
    including bool, which is almost always a mistake in a list of
    numbers even though it subclasses int.
    """
    total = 0
    for index, value in enumerate(numbers):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(
                "sum_even_numbers expected int or float, got "
                f"{type(value).__name__} at index {index}: {value!r}"
            )
        if isinstance(value, float):
            if not value.is_integer():
                continue
            value = int(value)
        if value % 2 == 0:
            total += value
    return total


def main(argv):
    try:
        numbers = [float(arg) if "." in arg else int(arg) for arg in argv]
    except ValueError as exc:
        print(f"error: arguments must be numbers ({exc})", file=sys.stderr)
        return 1
    print(sum_even_numbers(numbers))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
