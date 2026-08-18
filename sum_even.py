"""Sum the even numbers in a list.

Usage:
    from sum_even import sum_even_numbers

    sum_even_numbers([1, 2, 3, 4])  # -> 6
"""

from numbers import Integral


def sum_even_numbers(numbers):
    """Return the sum of the even numbers in ``numbers``.

    Args:
        numbers: An iterable of numbers. Integral values (``int``, ``bool``
            and other ``numbers.Integral`` types) are tested for evenness;
            floats with an integral value such as ``4.0`` also count as even.

    Returns:
        The sum of the even values, or ``0`` if there are none.

    Raises:
        TypeError: If an item is not a real number.
    """
    total = 0
    for item in numbers:
        if isinstance(item, Integral):
            if item % 2 == 0:
                total += item
        elif isinstance(item, float):
            if item.is_integer() and item % 2 == 0:
                total += item
        else:
            raise TypeError(f"expected a real number, got {type(item).__name__}")
    return total


if __name__ == "__main__":
    print(sum_even_numbers([1, 2, 3, 4, 5, 6]))
