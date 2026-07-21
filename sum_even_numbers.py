"""
Sum the even numbers in a list.

Pure standard library.
"""


def sum_even_numbers(numbers):
    """Return the sum of the even numbers in the given list.

    Floats with an integral value (e.g. 4.0) count as even; non-integral
    floats are skipped. Returns 0 for an empty list or a list with no
    even numbers.

    Raises TypeError if numbers is not a list, or if it contains a
    non-numeric value (str, None, bool, ...).
    """
    if not isinstance(numbers, list):
        raise TypeError(
            f"expected a list of numbers, got {type(numbers).__name__}"
        )
    total = 0
    for i, n in enumerate(numbers):
        if isinstance(n, bool) or not isinstance(n, (int, float)):
            raise TypeError(
                f"element at index {i} is not a number: {n!r}"
            )
        if isinstance(n, float):
            if not n.is_integer():
                continue
            n = int(n)
        if n % 2 == 0:
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
