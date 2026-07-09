"""Utility for summing the even numbers in a list."""


def sum_even_numbers(numbers):
    """Return the sum of the even numbers in the given list.

    Args:
        numbers: A list of numbers (ints or floats).

    Returns:
        The sum of the even numbers. Returns 0 if the list is empty
        or contains no even numbers.
    """
    return sum(n for n in numbers if isinstance(n, int) and not isinstance(n, bool) and n % 2 == 0)


if __name__ == "__main__":
    sample = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    print(f"Even numbers in {sample} sum to {sum_even_numbers(sample)}")
