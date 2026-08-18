"""Input validation for lists of integers.

Helpers that turn a caller-supplied list into a list of ``int``, with clear
errors when it holds non-integer values. Real values with a whole worth
(``4.0``, ``Fraction(4, 2)``, ``Decimal("4")``) are accepted and normalised
to the integer they represent; everything else is rejected.

Usage:
    from int_list import validate_int_list, filter_int_list, is_int_list

    validate_int_list([1, 2.0, 3])        # -> [1, 2, 3]
    validate_int_list([1, "2"])           # -> TypeError: values[1]: ...
    validate_int_list([1, 2.5])           # -> ValueError: values[1]: ...
    filter_int_list([1, "2", 3.5, 4])     # -> ([1, 4], [(1, '2'), (2, 3.5)])
    is_int_list([1, "2"])                 # -> False
"""

import math
from decimal import Decimal
from numbers import Integral, Real

__all__ = ["coerce_int", "validate_int_list", "filter_int_list", "is_int_list"]


def coerce_int(item):
    """Return ``item`` as an ``int``, or raise if it is not a whole number.

    Args:
        item: The value to check.

    Returns:
        The value as an ``int``.

    Raises:
        TypeError: If ``item`` is not a real number — strings, ``None``,
            complex numbers, ``bool`` and arbitrary objects all raise.
        ValueError: If ``item`` is a real number without a whole value,
            such as ``4.5``, ``nan`` or ``inf``.
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


def _iterate(values, name):
    """Return an iterator over ``values``, rejecting non-list-like inputs."""
    # Strings and bytes are iterable, but a string of digits is not a list.
    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError(
            f"{name}: expected a list of integers, got {type(values).__name__}: {values!r}"
        )
    try:
        return iter(values)
    except TypeError:
        raise TypeError(
            f"{name}: expected a list of integers, got {type(values).__name__}: {values!r}"
        ) from None


def validate_int_list(values, name="values", allow_empty=True):
    """Validate ``values`` as a list of integers and return it as ``list[int]``.

    Args:
        values: An iterable of integers. Real values with a whole worth, such
            as ``4.0``, ``Fraction(4, 2)`` or ``Decimal("4")``, are accepted
            and returned as the integer they represent.
        name: Label used in error messages to identify the offending
            argument, e.g. ``"numbers"`` -> ``"numbers[2]: ..."``.
        allow_empty: When ``False``, an empty ``values`` raises ``ValueError``.

    Returns:
        A new list containing every item as an ``int``.

    Raises:
        TypeError: If ``values`` is not an iterable (or is a string or bytes),
            or if any item is not a real number.
        ValueError: If any item is a real number without a whole value, or if
            ``values`` is empty and ``allow_empty`` is ``False``.
    """
    result = []
    for index, item in enumerate(_iterate(values, name)):
        try:
            result.append(coerce_int(item))
        except (TypeError, ValueError) as exc:
            raise type(exc)(f"{name}[{index}]: {exc}") from None
    if not result and not allow_empty:
        raise ValueError(f"{name}: expected at least one integer, got an empty list")
    return result


def filter_int_list(values, name="values"):
    """Split ``values`` into the integers it holds and the items it does not.

    Use this instead of :func:`validate_int_list` when non-integer values
    should be reported rather than raised on.

    Args:
        values: An iterable of candidate integers.
        name: Label used in the error message if ``values`` itself is not a
            list-like iterable.

    Returns:
        A ``(integers, rejected)`` tuple. ``integers`` is a list of ``int``,
        and ``rejected`` is a list of ``(index, item)`` pairs, in the order
        they appeared, for every item that is not a whole number.

    Raises:
        TypeError: If ``values`` is not an iterable, or is a string or bytes.
    """
    integers, rejected = [], []
    for index, item in enumerate(_iterate(values, name)):
        try:
            integers.append(coerce_int(item))
        except (TypeError, ValueError):
            rejected.append((index, item))
    return integers, rejected


def is_int_list(values, allow_empty=True):
    """Return ``True`` if ``values`` is a list of integers, else ``False``.

    A non-raising counterpart to :func:`validate_int_list`, for callers that
    want to branch on validity rather than handle an exception.
    """
    try:
        validate_int_list(values, allow_empty=allow_empty)
    except (TypeError, ValueError):
        return False
    return True


if __name__ == "__main__":
    print(validate_int_list([1, 2.0, 3]))
    print(filter_int_list([1, "2", 3.5, 4]))
