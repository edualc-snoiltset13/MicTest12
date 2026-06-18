def sum_even(numbers):
    """Return the sum of only the even numbers in the given list.

    Args:
        numbers: A list (or any iterable) of numbers.

    Returns:
        The sum of the even numbers. Returns 0 if there are none.
    """
    return sum(n for n in numbers if n % 2 == 0)


if __name__ == "__main__":
    print(sum_even([1, 2, 3, 4, 5, 6]))  # 12
    print(sum_even([1, 3, 5]))           # 0
    print(sum_even([]))                  # 0
