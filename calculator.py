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
    from history import CalculationHistory

    hist = CalculationHistory()
    print("Python Calculator")
    print("Supported operators: +, -, *, /, **, %")
    print("Commands: 'history' | 'last N' | 'search TERM' | 'clear' | 'quit'")
    while True:
        expr = input("\nEnter expression (or command): ").strip()
        if expr.lower() == "quit":
            break
        if expr.lower() == "history":
            entries = hist.get_all()
            if not entries:
                print("No history yet.")
            for i, e in enumerate(entries, 1):
                print(f"  {i}. {e['expression']} = {e['result']}  ({e['timestamp']})")
            continue
        if expr.lower().startswith("last"):
            parts = expr.split()
            n = int(parts[1]) if len(parts) > 1 else 1
            for e in hist.get_last(n):
                print(f"  {e['expression']} = {e['result']}  ({e['timestamp']})")
            continue
        if expr.lower().startswith("search"):
            query = expr[7:].strip()
            results = hist.search(query)
            if not results:
                print(f"No results for '{query}'.")
            for e in results:
                print(f"  {e['expression']} = {e['result']}")
            continue
        if expr.lower() == "clear":
            hist.clear()
            print("History cleared.")
            continue
        try:
            parts = expr.split()
            if len(parts) != 3:
                print("Format: <number> <operator> <number>")
                continue
            a, op, b = float(parts[0]), parts[1], float(parts[2])
            result = calculate(a, op, b)
            hist.record(a, op, b, result)
            print(f"= {result}")
        except ValueError as e:
            print(f"Error: {e}")
