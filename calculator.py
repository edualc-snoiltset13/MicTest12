def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def power(a, b):
    return a ** b


def modulo(a, b):
    if b == 0:
        raise ValueError("Cannot modulo by zero")
    return a % b


def calculate(a, operator, b):
    operations = {
        "+": add,
        "-": subtract,
        "*": multiply,
        "/": divide,
        "**": power,
        "%": modulo,
    }
    if operator not in operations:
        raise ValueError(f"Unknown operator: {operator}")
    return operations[operator](a, b)


if __name__ == "__main__":
    print("Python Calculator")
    print("Supported operators: +, -, *, /, **, %")
    while True:
        expr = input("\nEnter expression (or 'quit'): ").strip()
        if expr.lower() == "quit":
            break
        try:
            parts = expr.split()
            if len(parts) != 3:
                print("Format: <number> <operator> <number>")
                continue
            a, op, b = float(parts[0]), parts[1], float(parts[2])
            result = calculate(a, op, b)
            print(f"= {result}")
        except ValueError as e:
            print(f"Error: {e}")
