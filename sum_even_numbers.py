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
    """
    return sum(n for n in numbers if n % 2 == 0)


if __name__ == "__main__":
    sample = [1, 2, 3, 4, 5, 6]
    print(f"Even sum of {sample}: {sum_even_numbers(sample)}")
