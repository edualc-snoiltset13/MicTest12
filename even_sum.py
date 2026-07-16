"""
Sum the even numbers in a list. Pure standard library.
"""


def sum_even_numbers(numbers):
    """Return the sum of the even numbers in `numbers`.

    Odd numbers are ignored. An empty list (or one with no even
    numbers) sums to 0.

    Every element must be an integer; a non-integer value (including
    bool, float, str, None, ...) raises TypeError naming the offending
    value and its position.
    """
    for i, n in enumerate(numbers):
        if not isinstance(n, int) or isinstance(n, bool):
            raise TypeError(
                "sum_even_numbers expects integers, got "
                f"{type(n).__name__} {n!r} at index {i}"
            )
    return sum(n for n in numbers if n % 2 == 0)


if __name__ == "__main__":
    print(sum_even_numbers([1, 2, 3, 4, 5, 6]))  # 12
