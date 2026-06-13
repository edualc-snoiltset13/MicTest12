"""
Simple class-based calculator.

Provides arithmetic methods, a memory register, and an operation history.
Pure standard library.
"""


def _as_number(name, value):
    """Validate that ``value`` is a real number and return it.

    Rejects ``bool`` (a subclass of ``int``) and any non-numeric type so
    that arithmetic methods never silently fall back to string/sequence
    behaviour (e.g. ``"a" + "b"`` or ``"x" * 3``).
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(
            f"{name} must be an int or float, got {type(value).__name__}"
        )
    return value


class Calculator:
    def __init__(self):
        self.memory = 0
        self.history = []

    def add(self, a, b):
        a, b = _as_number("a", a), _as_number("b", b)
        result = a + b
        self._record("add", a, b, result)
        return result

    def subtract(self, a, b):
        a, b = _as_number("a", a), _as_number("b", b)
        result = a - b
        self._record("subtract", a, b, result)
        return result

    def multiply(self, a, b):
        a, b = _as_number("a", a), _as_number("b", b)
        result = a * b
        self._record("multiply", a, b, result)
        return result

    def divide(self, a, b):
        a, b = _as_number("a", a), _as_number("b", b)
        if b == 0:
            raise ValueError("division by zero")
        result = a / b
        self._record("divide", a, b, result)
        return result

    def power(self, a, b):
        a, b = _as_number("a", a), _as_number("b", b)
        result = a ** b
        self._record("power", a, b, result)
        return result

    def modulo(self, a, b):
        a, b = _as_number("a", a), _as_number("b", b)
        if b == 0:
            raise ValueError("modulo by zero")
        result = a % b
        self._record("modulo", a, b, result)
        return result

    def store(self, value):
        self.memory = _as_number("value", value)

    def recall(self):
        return self.memory

    def clear_memory(self):
        self.memory = 0

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
    print("Simple Calculator — enter '<a> <op> <b>' (e.g. '3 + 4'), or 'quit'.")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if line in ("quit", "exit", ""):
            return
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
