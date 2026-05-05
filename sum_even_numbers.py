def sum_even_numbers(numbers):
    for n in numbers:
        if not isinstance(n, int) or isinstance(n, bool):
            raise TypeError(f"All elements must be integers, got {type(n).__name__}: {n!r}")
    return sum(n for n in numbers if n % 2 == 0)
