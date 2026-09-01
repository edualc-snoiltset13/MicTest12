"""
Sum the even numbers in a list.

Stdlib-only helper: `sum_even_numbers([1, 2, 3, 4]) -> 6`.

Input is validated element by element — every value must be an integer, so
bad data raises instead of being silently skipped. Errors name the offending
index, which is what you want when the list came from a file or a form.
"""

import math


def _as_integer(index, value):
    """Return `value` as an int, or raise explaining why it is not one.

    Booleans are rejected on purpose: Python makes `True` an int, so a stray
    `False` would otherwise be summed as an even number.
    """
    if isinstance(value, bool):
        raise TypeError(
            "item {}: expected an integer, got bool {!r}".format(index, value)
        )
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValueError(
                "item {}: expected a finite integer, got {!r}".format(index, value)
            )
        if not value.is_integer():
            raise ValueError(
                "item {}: expected an integer, got fractional {!r}".format(index, value)
            )
        return int(value)
    raise TypeError(
        "item {}: expected an integer, got {} {!r}".format(
            index, type(value).__name__, value
        )
    )


def sum_even_numbers(numbers):
    """Return the sum of the even numbers in `numbers`.

    Accepts any iterable of integers; whole floats count as integers (4.0 is
    4, 4.5 is not an integer). An empty iterable — or one with no even values
    — sums to 0. The result is always an int.

    Raises TypeError if `numbers` is not iterable, or if an element is not a
    number (a bool included). Raises ValueError if an element is a number but
    not a finite whole one. Both messages name the index of the bad element.
    """
    try:
        items = enumerate(numbers)
    except TypeError:
        raise TypeError(
            "expected an iterable of integers, got {} {!r}".format(
                type(numbers).__name__, numbers
            )
        ) from None

    total = 0
    for index, value in items:
        number = _as_integer(index, value)
        if number % 2 == 0:
            total += number
    return total


if __name__ == "__main__":
    print(sum_even_numbers([1, 2, 3, 4, 5, 6]))  # 12
