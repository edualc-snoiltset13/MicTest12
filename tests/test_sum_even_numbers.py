"""Unit tests for sum_even_numbers.

Stdlib-only: run with `python -m unittest discover -s tests`.
"""

import sys
import unittest
from pathlib import Path

# Make the project root importable when run from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sum_even_numbers import sum_even_numbers  # noqa: E402


class SumEvenNumbersTests(unittest.TestCase):
    def test_mixed_list(self):
        self.assertEqual(sum_even_numbers([1, 2, 3, 4, 5, 6]), 12)

    def test_empty_list(self):
        self.assertEqual(sum_even_numbers([]), 0)

    def test_no_even_numbers(self):
        self.assertEqual(sum_even_numbers([1, 3, 5]), 0)

    def test_negative_and_zero(self):
        self.assertEqual(sum_even_numbers([-4, -3, 0, 3]), -4)

    def test_accepts_any_iterable(self):
        self.assertEqual(sum_even_numbers(range(1, 7)), 12)

    def test_whole_floats_count_as_integers(self):
        result = sum_even_numbers([2.0, 3.0, 4.0])
        self.assertEqual(result, 6)
        self.assertIsInstance(result, int)


class ValidationTests(unittest.TestCase):
    def test_non_iterable_input_rejected(self):
        with self.assertRaises(TypeError) as ctx:
            sum_even_numbers(42)
        self.assertIn("iterable", str(ctx.exception))

    def test_none_input_rejected(self):
        with self.assertRaises(TypeError):
            sum_even_numbers(None)

    def test_string_element_rejected(self):
        with self.assertRaises(TypeError) as ctx:
            sum_even_numbers([2, "4"])
        self.assertIn("str", str(ctx.exception))

    def test_none_element_rejected(self):
        with self.assertRaises(TypeError):
            sum_even_numbers([2, None])

    def test_booleans_rejected(self):
        with self.assertRaises(TypeError) as ctx:
            sum_even_numbers([True, 2])
        self.assertIn("bool", str(ctx.exception))

    def test_fractional_float_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            sum_even_numbers([2, 4.5])
        self.assertIn("fractional", str(ctx.exception))

    def test_nan_rejected(self):
        with self.assertRaises(ValueError):
            sum_even_numbers([2, float("nan")])

    def test_infinity_rejected(self):
        with self.assertRaises(ValueError):
            sum_even_numbers([2, float("inf")])

    def test_error_names_the_offending_index(self):
        with self.assertRaises(TypeError) as ctx:
            sum_even_numbers([0, 2, 4, "six"])
        self.assertIn("item 3", str(ctx.exception))

    def test_validation_precedes_the_even_check(self):
        # An odd invalid value still raises — it is not skipped as "not even".
        with self.assertRaises(TypeError):
            sum_even_numbers([2, "3"])


if __name__ == "__main__":
    unittest.main()
