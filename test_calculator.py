"""
Basic arithmetic tests for calculator.evaluate.

Run:
    python -m unittest test_calculator
"""

import unittest

from calculator import evaluate


class BasicArithmeticTests(unittest.TestCase):
    cases = [
        # (expression, expected)
        ("2 + 3",          5),
        ("10 - 4",         6),
        ("6 * 7",          42),
        ("20 / 4",         5),
        ("10 / 4",         2.5),
        ("10 // 3",        3),
        ("10 % 3",         1),
        ("2 ** 8",         256),
        ("2 + 3 * 4",      14),
        ("(2 + 3) * 4",    20),
        ("-3 + 5",         2),
        ("-(2 + 3)",       -5),
    ]

    def test_basic_arithmetic(self):
        for expr, expected in self.cases:
            with self.subTest(expr=expr):
                self.assertAlmostEqual(evaluate(expr), expected, places=9)


if __name__ == "__main__":
    unittest.main(verbosity=2)
