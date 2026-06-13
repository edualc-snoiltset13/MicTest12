"""
Simple Python calculator.

Supports basic arithmetic, exponentiation, modulo, square root, and a
small interactive REPL. Pure standard library.

Usage:
    python calculator.py                 # interactive REPL
    python calculator.py "2 + 3 * 4"     # evaluate one expression and exit
"""

import math
import operator
import re
import sys

BINARY_OPS = {
    "+":  operator.add,
    "-":  operator.sub,
    "*":  operator.mul,
    "/":  operator.truediv,
    "//": operator.floordiv,
    "%":  operator.mod,
    "**": operator.pow,
}

UNARY_OPS = {
    "u-": operator.neg,
}

PRECEDENCE = {
    "+": 1, "-": 1,
    "*": 2, "/": 2, "//": 2, "%": 2,
    "u-": 3,
    "**": 4,
}

RIGHT_ASSOC = {"**", "u-"}

FUNCTIONS = {
    "sqrt": math.sqrt,
    "abs":  abs,
}

TOKEN_RE = re.compile(
    r"\s*(?:"
    r"(?P<number>\d+\.\d+|\.\d+|\d+)"
    r"|(?P<func>sqrt|abs)"
    r"|(?P<op>\*\*|//|[+\-*/%()])"
    r")"
)


def tokenize(expr):
    tokens = []
    pos = 0
    while pos < len(expr):
        m = TOKEN_RE.match(expr, pos)
        if not m or m.end() == pos:
            raise ValueError(f"unexpected character at position {pos}: {expr[pos]!r}")
        if m.group("number"):
            tokens.append(("num", float(m.group("number"))))
        elif m.group("func"):
            tokens.append(("func", m.group("func")))
        else:
            tokens.append(("op", m.group("op")))
        pos = m.end()
    return tokens


def to_rpn(tokens):
    """Shunting-yard: convert infix tokens to Reverse Polish Notation."""
    output, stack = [], []
    prev = None
    for kind, value in tokens:
        if kind == "num":
            output.append((kind, value))
        elif kind == "func":
            stack.append((kind, value))
        elif kind == "op":
            if value == "(":
                stack.append((kind, value))
            elif value == ")":
                while stack and stack[-1] != ("op", "("):
                    output.append(stack.pop())
                if not stack:
                    raise ValueError("unbalanced parentheses")
                stack.pop()
                if stack and stack[-1][0] == "func":
                    output.append(stack.pop())
            else:
                # Detect unary minus / plus.
                is_unary = value in ("+", "-") and (
                    prev is None
                    or prev == ("op", "(")
                    or (prev and prev[0] == "op" and prev[1] != ")")
                )
                if is_unary:
                    op_value = "u-" if value == "-" else None
                    if op_value is None:
                        prev = (kind, value)
                        continue  # unary plus is a no-op
                else:
                    op_value = value
                while stack and stack[-1][0] == "op" and stack[-1][1] != "(":
                    top_op = stack[-1][1]
                    if (PRECEDENCE[top_op] > PRECEDENCE[op_value] or
                        (PRECEDENCE[top_op] == PRECEDENCE[op_value] and op_value not in RIGHT_ASSOC)):
                        output.append(stack.pop())
                    else:
                        break
                stack.append(("op", op_value))
        prev = (kind, value)

    while stack:
        top = stack.pop()
        if top == ("op", "(") or top == ("op", ")"):
            raise ValueError("unbalanced parentheses")
        output.append(top)
    return output


def eval_rpn(rpn):
    stack = []
    for kind, value in rpn:
        if kind == "num":
            stack.append(value)
        elif kind == "func":
            if not stack:
                raise ValueError(f"missing argument for {value}")
            stack.append(FUNCTIONS[value](stack.pop()))
        elif value in UNARY_OPS:
            if not stack:
                raise ValueError(f"missing operand for unary {value}")
            stack.append(UNARY_OPS[value](stack.pop()))
        else:  # binary op
            if len(stack) < 2:
                raise ValueError(f"missing operand for {value}")
            b = stack.pop()
            a = stack.pop()
            try:
                stack.append(BINARY_OPS[value](a, b))
            except ZeroDivisionError:
                raise ValueError("division by zero")
            except OverflowError:
                raise ValueError("numeric overflow")
    if len(stack) != 1:
        raise ValueError("invalid expression")
    return stack[0]


def evaluate(expr):
    """Evaluate an arithmetic expression and return a float."""
    return eval_rpn(to_rpn(tokenize(expr)))


def _format(result):
    if isinstance(result, float) and result.is_integer():
        return str(int(result))
    return str(result)


def repl():
    print("Calculator — type an expression, 'help', or 'quit'.")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not line:
            continue
        if line in ("quit", "exit"):
            return
        if line == "help":
            print("Operators: + - * / // % **")
            print("Functions: sqrt(x), abs(x)")
            print("Parentheses are supported.")
            continue
        try:
            print(_format(evaluate(line)))
        except ValueError as e:
            print(f"error: {e}")


def main(argv):
    if len(argv) > 1:
        try:
            print(_format(evaluate(" ".join(argv[1:]))))
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        repl()


if __name__ == "__main__":
    main(sys.argv)
