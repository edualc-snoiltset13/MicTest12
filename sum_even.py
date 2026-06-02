def sum_even(numbers):
    """Return the sum of only the even integers in the given list.

    Args:
        numbers: An iterable of integers.

    Returns:
        The sum of the even integers. Returns 0 if there are none.

    Raises:
        TypeError: If ``numbers`` is not iterable, or if any element is not
            an integer. Booleans are rejected since they are not meaningful
            integers in this context.
    """
    try:
        iterator = iter(numbers)
    except TypeError:
        raise TypeError(
            f"expected an iterable of integers, got {type(numbers).__name__}"
        )

    total = 0
    for index, value in enumerate(iterator):
        # bool is a subclass of int, but treating True/False as numbers is
        # almost never intended, so reject it explicitly.
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(
                f"non-integer value at index {index}: "
                f"{value!r} ({type(value).__name__})"
            )
        if value % 2 == 0:
            total += value

    return total
