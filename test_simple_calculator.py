"""
Tests for simple_calculator.Calculator.

Run:
    python -m unittest test_simple_calculator
"""

import unittest

from simple_calculator import Calculator


class CalculatorHistoryTests(unittest.TestCase):
    def test_get_history_empty_by_default(self):
        calc = Calculator()
        self.assertEqual(calc.get_history(), [])

    def test_get_history_records_each_operation(self):
        calc = Calculator()
        calc.add(2, 3)
        calc.multiply(4, 5)
        calc.divide(10, 2)

        entries = calc.get_history()
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0], {"op": "add", "a": 2, "b": 3, "result": 5})
        self.assertEqual(entries[1], {"op": "multiply", "a": 4, "b": 5, "result": 20})
        self.assertEqual(entries[2], {"op": "divide", "a": 10, "b": 2, "result": 5})

    def test_get_history_is_defensive_copy(self):
        calc = Calculator()
        calc.add(1, 1)

        snapshot = calc.get_history()
        snapshot.clear()
        snapshot_again = calc.get_history()
        self.assertEqual(len(snapshot_again), 1)

        snapshot_again[0]["op"] = "tampered"
        self.assertEqual(calc.get_history()[0]["op"], "add")

    def test_failed_operation_is_not_recorded(self):
        calc = Calculator()
        with self.assertRaises(ValueError):
            calc.divide(1, 0)
        self.assertEqual(calc.get_history(), [])

    def test_clear_history_empties_history(self):
        calc = Calculator()
        calc.add(1, 2)
        calc.clear_history()
        self.assertEqual(calc.get_history(), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
