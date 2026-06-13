"""
Tests for the class-based Calculator in simple_calculator.py.

Run:
    python -m unittest test_simple_calculator
"""

import unittest

from simple_calculator import Calculator


class ArithmeticTests(unittest.TestCase):
    def setUp(self):
        self.calc = Calculator()

    def test_basic_operations(self):
        self.assertEqual(self.calc.add(2, 3), 5)
        self.assertEqual(self.calc.subtract(10, 4), 6)
        self.assertEqual(self.calc.multiply(6, 7), 42)
        self.assertEqual(self.calc.divide(20, 4), 5)
        self.assertEqual(self.calc.power(2, 8), 256)
        self.assertEqual(self.calc.modulo(10, 3), 1)

    def test_divide_by_zero_raises(self):
        with self.assertRaises(ValueError):
            self.calc.divide(1, 0)

    def test_modulo_by_zero_raises(self):
        with self.assertRaises(ValueError):
            self.calc.modulo(1, 0)


class InputValidationTests(unittest.TestCase):
    def setUp(self):
        self.calc = Calculator()

    BINARY_METHODS = ("add", "subtract", "multiply", "divide", "power", "modulo")

    def test_string_arguments_rejected(self):
        for name in self.BINARY_METHODS:
            method = getattr(self.calc, name)
            with self.subTest(method=name):
                with self.assertRaises(TypeError):
                    method("a", "b")

    def test_non_numeric_types_rejected(self):
        for bad in ("x", None, [1], {"a": 1}, (1,)):
            with self.subTest(value=bad):
                with self.assertRaises(TypeError):
                    self.calc.add(bad, 1)
                with self.assertRaises(TypeError):
                    self.calc.add(1, bad)

    def test_bool_rejected(self):
        # bool is a subclass of int but is not a valid numeric operand here.
        with self.assertRaises(TypeError):
            self.calc.add(True, 1)
        with self.assertRaises(TypeError):
            self.calc.multiply(1, False)

    def test_float_and_int_accepted(self):
        self.assertAlmostEqual(self.calc.add(1.5, 2), 3.5)
        self.assertAlmostEqual(self.calc.multiply(2.0, 3.0), 6.0)

    def test_store_validates_input(self):
        with self.assertRaises(TypeError):
            self.calc.store("not a number")
        self.calc.store(42)
        self.assertEqual(self.calc.recall(), 42)

    def test_validation_failure_does_not_record_history(self):
        with self.assertRaises(TypeError):
            self.calc.add("a", "b")
        self.assertEqual(self.calc.history, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
