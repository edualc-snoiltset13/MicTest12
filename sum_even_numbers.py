from functools import reduce


def sum_even_numbers(numbers):
    return reduce(lambda acc, n: acc + n, filter(lambda n: n % 2 == 0, numbers), 0)
