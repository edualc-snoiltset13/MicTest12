"""
Sum the even numbers in a list. Pure standard library.
"""


def sum_even_numbers(numbers):
    """Return the sum of the even numbers in `numbers`.

    Odd numbers are ignored. An empty list (or one with no even
    numbers) sums to 0.
    """
    return sum(n for n in numbers if n % 2 == 0)


if __name__ == "__main__":
    print(sum_even_numbers([1, 2, 3, 4, 5, 6]))  # 12
