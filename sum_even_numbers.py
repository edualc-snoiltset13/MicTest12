"""
Sum the even numbers in a list.

Pure standard library.
"""


def sum_even_numbers(numbers):
    """Return the sum of the even numbers in the given list.

    Only integers (including bools' parent type, and floats with an
    integral value) can be even; non-integral floats are skipped.
    Returns 0 for an empty list or a list with no even numbers.
    """
    total = 0
    for n in numbers:
        if isinstance(n, float):
            if not n.is_integer():
                continue
            n = int(n)
        if isinstance(n, int) and n % 2 == 0:
            total += n
    return total


def main():
    print("Sum of even numbers — enter numbers separated by spaces, or 'quit'.")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if line in ("quit", "exit", ""):
            return
        try:
            numbers = [float(part) for part in line.split()]
        except ValueError:
            print("error: expected numbers separated by spaces")
            continue
        print(sum_even_numbers(numbers))


if __name__ == "__main__":
    main()
