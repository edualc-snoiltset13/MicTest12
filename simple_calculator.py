"""
Simple class-based calculator.

Provides arithmetic methods, a memory register, and an operation history.
Pure standard library.
"""


class Calculator:
    def __init__(self):
        self.memory = 0
        self.history = []

    def add(self, a, b):
        result = a + b
        self._record("add", a, b, result)
        return result

    def subtract(self, a, b):
        result = a - b
        self._record("subtract", a, b, result)
        return result

    def multiply(self, a, b):
        result = a * b
        self._record("multiply", a, b, result)
        return result

    def divide(self, a, b):
        if b == 0:
            raise ValueError("division by zero")
        result = a / b
        self._record("divide", a, b, result)
        return result

    def power(self, a, b):
        result = a ** b
        self._record("power", a, b, result)
        return result

    def modulo(self, a, b):
        if b == 0:
            raise ValueError("modulo by zero")
        result = a % b
        self._record("modulo", a, b, result)
        return result

    def store(self, value):
        self.memory = value

    def recall(self):
        return self.memory

    def clear_memory(self):
        self.memory = 0

    def get_history(self):
        # Defensive copy so callers can't mutate internal state.
        return [dict(entry) for entry in self.history]

    def clear_history(self):
        self.history.clear()

    def _record(self, op, a, b, result):
        self.history.append({"op": op, "a": a, "b": b, "result": result})


def main():
    calc = Calculator()
    ops = {
        "+": calc.add, "-": calc.subtract,
        "*": calc.multiply, "/": calc.divide,
        "**": calc.power, "%": calc.modulo,
    }
    print("Simple Calculator — enter '<a> <op> <b>' (e.g. '3 + 4'),")
    print("or 'history', 'clear', or 'quit'.")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if line in ("quit", "exit", ""):
            return
        if line == "history":
            entries = calc.get_history()
            if not entries:
                print("(no history)")
            else:
                for i, e in enumerate(entries, 1):
                    print(f"{i}. {e['a']} {e['op']} {e['b']} = {e['result']}")
            continue
        if line == "clear":
            calc.clear_history()
            print("(history cleared)")
            continue
        parts = line.split()
        if len(parts) != 3 or parts[1] not in ops:
            print(f"error: expected '<number> <{'/'.join(ops)}> <number>'")
            continue
        try:
            a = float(parts[0])
            b = float(parts[2])
            print(ops[parts[1]](a, b))
        except ValueError as e:
            print(f"error: {e}")


if __name__ == "__main__":
    main()
