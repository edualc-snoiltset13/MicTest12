def sum_even(numbers):
    """Return the sum of only the even numbers in the given list.

    Args:
        numbers: A list (or any iterable) of integers.

    Returns:
        The sum of the even numbers. Returns 0 if there are none.

    Raises:
        TypeError: If ``numbers`` is not iterable, or if it contains a value
            that is not an integer. Booleans are rejected even though they are
            technically a subclass of ``int``.
    """
    try:
        iterator = iter(numbers)
    except TypeError:
        raise TypeError(
            f"expected an iterable of integers, got {type(numbers).__name__}"
        )

    total = 0
    for index, value in enumerate(iterator):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(
                f"non-integer value at index {index}: "
                f"{value!r} ({type(value).__name__})"
            )
        if value % 2 == 0:
            total += value
    return total


if __name__ == "__main__":
    print(sum_even([1, 2, 3, 4, 5, 6]))  # 12
    print(sum_even([1, 3, 5]))           # 0
    print(sum_even([]))                  # 0
