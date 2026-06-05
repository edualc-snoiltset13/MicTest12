from numbers import Number


def divide(a, b):
    """Divide ``a`` by ``b`` and return the result.

    Args:
        a: The numerator (an int or float).
        b: The denominator (an int or float).

    Returns:
        The quotient ``a / b``.

    Raises:
        TypeError: If ``a`` or ``b`` is not a number. Booleans are rejected
            since treating True/False as numbers is almost never intended.
        ZeroDivisionError: If ``b`` is zero.
    """
    for name, value in (("a", a), ("b", b)):
        if isinstance(value, bool) or not isinstance(value, Number):
            raise TypeError(
                f"{name} must be a number, got {type(value).__name__}"
            )

    if b == 0:
        raise ZeroDivisionError("cannot divide by zero")

    return a / b
