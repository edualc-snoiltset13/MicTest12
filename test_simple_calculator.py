"""
Tests for simple_calculator.Calculator.

Run:
    python -m unittest test_simple_calculator
"""

import unittest

from simple_calculator import Calculator


class CalculatorTests(unittest.TestCase):
    def setUp(self):
        self.calc = Calculator()

    def test_basic_operations(self):
        self.assertEqual(self.calc.add(2, 3), 5)
        self.assertEqual(self.calc.subtract(10, 4), 6)
        self.assertEqual(self.calc.multiply(6, 7), 42)
        self.assertEqual(self.calc.divide(20, 4), 5)
        self.assertEqual(self.calc.power(2, 8), 256)
        self.assertEqual(self.calc.modulo(10, 3), 1)

    def test_floor_divide(self):
        self.assertEqual(self.calc.floor_divide(10, 3), 3)
        self.assertEqual(self.calc.floor_divide(7, 2), 3)
        self.assertEqual(self.calc.floor_divide(-7, 2), -4)

    def test_floor_divide_by_zero_raises(self):
        with self.assertRaises(ValueError):
            self.calc.floor_divide(1, 0)

    def test_divide_by_zero_raises(self):
        with self.assertRaises(ValueError):
            self.calc.divide(1, 0)

    def test_history_records_operations(self):
        self.calc.add(1, 2)
        self.calc.floor_divide(9, 2)
        self.assertEqual(len(self.calc.history), 2)
        self.assertEqual(self.calc.history[-1],
                         {"op": "floor_divide", "a": 9, "b": 2, "result": 4})

    def test_memory_register(self):
        self.calc.store(42)
        self.assertEqual(self.calc.recall(), 42)
        self.calc.clear_memory()
        self.assertEqual(self.calc.recall(), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
