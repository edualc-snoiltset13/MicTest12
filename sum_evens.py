def sum_even_numbers(numbers):
    if not isinstance(numbers, (list, tuple)):
        raise TypeError(f"expected a list or tuple, got {type(numbers).__name__}")
    for i, n in enumerate(numbers):
        if isinstance(n, bool) or not isinstance(n, int):
            raise TypeError(f"non-integer value at index {i}: {n!r}")
    return sum(n for n in numbers if n % 2 == 0)


if __name__ == "__main__":
    print(sum_even_numbers([1, 2, 3, 4, 5, 6]))  # 12
    print(sum_even_numbers([7, 11, 13]))         # 0
    print(sum_even_numbers([]))                  # 0
    try:
        sum_even_numbers([1, 2, "3", 4])
    except TypeError as e:
        print(f"TypeError: {e}")
