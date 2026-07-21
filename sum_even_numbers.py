"""
Sum the even numbers in a list.

Pure standard library.
"""


def sum_even_numbers(numbers):
    """Return the sum of the even numbers in the given list.

    Args:
        numbers: A list (or any iterable) of integers.

    Returns:
        The sum of the even values; 0 if there are none.

    Raises:
        TypeError: If `numbers` is not iterable, or if any element is not
            an integer (bool is rejected too, since True/False are not
            meaningful here despite being int subclasses).
    """
    if not hasattr(numbers, "__iter__"):
        raise TypeError(
            f"numbers must be an iterable of integers, got {type(numbers).__name__}"
        )

    total = 0
    for index, n in enumerate(numbers):
        if isinstance(n, bool) or not isinstance(n, int):
            raise TypeError(
                f"all elements must be integers, but element at index {index} "
                f"is {type(n).__name__}: {n!r}"
            )
        if n % 2 == 0:
            total += n
    return total


if __name__ == "__main__":
    sample = [1, 2, 3, 4, 5, 6]
    print(f"Even sum of {sample}: {sum_even_numbers(sample)}")
