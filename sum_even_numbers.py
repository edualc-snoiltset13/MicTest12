"""
Sum the even numbers in a list.

Pure standard library.

Usage:
    python sum_even_numbers.py 1 2 3 4 5 6   # prints 12
"""

import sys


def sum_even_numbers(numbers):
    """Return the sum of the even numbers in *numbers*.

    Accepts any iterable of numbers. Floats are included only when they
    are whole and even (e.g. 4.0 counts, 4.5 does not). Booleans are
    treated as the integers 0 and 1, so they never contribute.
    """
    total = 0
    for value in numbers:
        if isinstance(value, float):
            if not value.is_integer():
                continue
            value = int(value)
        if value % 2 == 0:
            total += value
    return total


def main(argv):
    numbers = [float(arg) if "." in arg else int(arg) for arg in argv]
    print(sum_even_numbers(numbers))


if __name__ == "__main__":
    main(sys.argv[1:])
