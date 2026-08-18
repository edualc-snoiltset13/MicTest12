"""Sum the even numbers in a list.

Usage:
    from sum_even import sum_even_numbers

    sum_even_numbers([1, 2, 3, 4])       # -> 6
    sum_even_numbers([1, "2"])           # -> TypeError
    sum_even_numbers([1, "2"], strict=False)  # -> 0 (bad items skipped)
"""

import math
from decimal import Decimal
from numbers import Integral, Real

__all__ = ["sum_even_numbers"]


def _as_int(item):
    """Return ``item`` as an ``int``, or raise if it is not a whole number.

    Raises:
        TypeError: If ``item`` is not a real number (strings, ``None``,
            complex numbers, ``bool``, arbitrary objects).
        ValueError: If ``item`` is a real number without a whole value
            (``4.5``, ``nan``, ``inf``).
    """
    # bool is a subclass of int, but True/False are not data points here.
    if isinstance(item, bool) or not isinstance(item, (Real, Decimal)):
        raise TypeError(f"expected an integer, got {type(item).__name__}: {item!r}")
    if isinstance(item, Integral):
        return int(item)
    if not math.isfinite(item):
        raise ValueError(f"expected an integer, got a non-finite value: {item!r}")
    value = float(item)
    if not value.is_integer():
        raise ValueError(f"expected an integer, got a fractional value: {item!r}")
    return int(value)


def sum_even_numbers(numbers, strict=True):
    """Return the sum of the even integers in ``numbers``.

    Args:
        numbers: An iterable of integers. Real values with a whole number
            worth, such as ``4.0``, ``Fraction(4, 2)`` or ``Decimal("4")``,
            are accepted and counted as the integer they represent.
        strict: When ``True`` (the default), any item that is not an integer
            raises. When ``False``, such items are skipped instead.

    Returns:
        The sum of the even values as an ``int``, or ``0`` if there are none.

    Raises:
        TypeError: If ``numbers`` is not an iterable (or is a string), or —
            when ``strict`` — if an item is not a real number.
        ValueError: When ``strict`` and an item is a real number without a
            whole value, such as ``4.5``, ``nan`` or ``inf``.
    """
    if isinstance(numbers, (str, bytes, bytearray)):
        raise TypeError(f"expected an iterable of numbers, got {type(numbers).__name__}")
    try:
        items = iter(numbers)
    except TypeError:
        raise TypeError(
            f"expected an iterable of numbers, got {type(numbers).__name__}"
        ) from None

    total = 0
    for index, item in enumerate(items):
        try:
            value = _as_int(item)
        except (TypeError, ValueError) as exc:
            if not strict:
                continue
            raise type(exc)(f"item {index}: {exc}") from None
        if value % 2 == 0:
            total += value
    return total


if __name__ == "__main__":
    print(sum_even_numbers([1, 2, 3, 4, 5, 6]))
