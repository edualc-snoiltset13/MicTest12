"""
Sum the even numbers in a list.

Stdlib-only helper: `sum_even_numbers([1, 2, 3, 4]) -> 6`.
"""


def sum_even_numbers(numbers):
    """Return the sum of the even numbers in `numbers`.

    Accepts any iterable of numbers. Integers and whole floats are both
    considered (4 and 4.0 are even, 4.5 is not). An empty iterable — or one
    with no even values — sums to 0.

    Raises TypeError if an element is not a number.
    """
    total = 0
    for value in numbers:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("expected a number, got {!r}".format(value))
        if value % 2 == 0:
            total += value
    return total


if __name__ == "__main__":
    print(sum_even_numbers([1, 2, 3, 4, 5, 6]))  # 12
