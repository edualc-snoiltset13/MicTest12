def sum_even_numbers(numbers):
    return sum(n for n in numbers if n % 2 == 0)


if __name__ == "__main__":
    print(sum_even_numbers([1, 2, 3, 4, 5, 6]))  # 12
    print(sum_even_numbers([7, 11, 13]))         # 0
    print(sum_even_numbers([]))                  # 0
