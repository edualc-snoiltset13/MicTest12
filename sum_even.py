from collections.abc import Iterable


def sum_even_numbers(numbers):
    if not isinstance(numbers, Iterable) or isinstance(numbers, (str, bytes)):
        raise TypeError(f"Expected an iterable of integers, got {type(numbers).__name__}")
    return sum(n for n in numbers if isinstance(n, int) and not isinstance(n, bool) and n % 2 == 0)


if __name__ == "__main__":
    print(sum_even_numbers([1, 2, 3, 4, 5, 6]))                # 12
    print(sum_even_numbers([7, 11, 13]))                        # 0
    print(sum_even_numbers([-2, -1, 0, 1, 2]))                  # 0
    print(sum_even_numbers([]))                                 # 0
    print(sum_even_numbers([2, "4", 6, None, 8.0, True, 10]))  # 18 (skips "4", None, 8.0, True)
    try:
        sum_even_numbers("123")
    except TypeError as e:
        print(f"TypeError: {e}")
    try:
        sum_even_numbers(42)
    except TypeError as e:
        print(f"TypeError: {e}")
