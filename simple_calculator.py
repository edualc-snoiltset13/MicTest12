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

    def clear_history(self):
        self.history.clear()

    def _record(self, op, a, b, result):
        self.history.append({"op": op, "a": a, "b": b, "result": result})


_QUIT = object()  # sentinel returned by process_command to signal exit


def _format_history(history):
    if not history:
        return "(history empty)"
    lines = []
    for i, h in enumerate(history, 1):
        lines.append(f"{i}. {h['a']} {h['op']} {h['b']} = {h['result']}")
    return "\n".join(lines)


def process_command(calc, line):
    """Process a single REPL command against ``calc``.

    Returns a string to display, or the ``_QUIT`` sentinel to exit.
    The token ``mem`` may be used in place of either operand to refer to
    the current memory value (e.g. ``mem + 3``).
    """
    ops = {
        "+": calc.add, "-": calc.subtract,
        "*": calc.multiply, "/": calc.divide,
        "**": calc.power, "%": calc.modulo,
    }
    line = line.strip()
    if line in ("quit", "exit", ""):
        return _QUIT

    parts = line.split()
    command = parts[0].lower()

    # Memory / history commands.
    if command == "recall":
        return str(calc.recall())
    if command == "store":
        if not calc.history:
            return "error: no result to store"
        calc.store(calc.history[-1]["result"])
        return f"stored {calc.recall()} in memory"
    if command == "clearmem":
        calc.clear_memory()
        return "memory cleared"
    if command == "history":
        return _format_history(calc.history)
    if command == "clearhist":
        calc.clear_history()
        return "history cleared"
    if command == "help":
        return (
            "commands: <a> <op> <b> | recall | store | clearmem | "
            "history | clearhist | help | quit\n"
            f"operators: {' '.join(ops)} (use 'mem' as an operand for memory)"
        )

    # Arithmetic: '<a> <op> <b>'.
    if len(parts) != 3 or parts[1] not in ops:
        return f"error: expected '<number> <{'/'.join(ops)}> <number>'"

    def _operand(token):
        return calc.recall() if token.lower() == "mem" else float(token)

    try:
        a = _operand(parts[0])
        b = _operand(parts[2])
        return str(ops[parts[1]](a, b))
    except ValueError as e:
        return f"error: {e}"


def main():
    calc = Calculator()
    print(
        "Simple Calculator — enter '<a> <op> <b>' (e.g. '3 + 4'), "
        "'help' for commands, or 'quit'."
    )
    while True:
        try:
            line = input("> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        result = process_command(calc, line)
        if result is _QUIT:
            return
        print(result)


if __name__ == "__main__":
    main()
