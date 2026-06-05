def divide(a, b):
    """Divide ``a`` by ``b`` and return the result.

    Args:
        a: The numerator.
        b: The denominator.

    Returns:
        The quotient ``a / b``.

    Raises:
        ZeroDivisionError: If ``b`` is zero.
    """
    if b == 0:
        raise ZeroDivisionError("cannot divide by zero")
    return a / b
