"""Unit tests for sum_even.

Stdlib-only: run with `python -m unittest discover -s tests`.
"""

import sys
import unittest
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

# Make the project root importable when run from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sum_even import sum_even_numbers  # noqa: E402


class TestSumEvenNumbers(unittest.TestCase):
    def test_mixed_list(self):
        self.assertEqual(sum_even_numbers([1, 2, 3, 4, 5, 6]), 12)

    def test_empty_list(self):
        self.assertEqual(sum_even_numbers([]), 0)

    def test_no_even_numbers(self):
        self.assertEqual(sum_even_numbers([1, 3, 5, 7]), 0)

    def test_negative_numbers(self):
        self.assertEqual(sum_even_numbers([-2, -3, -4]), -6)

    def test_zero_counts_as_even(self):
        self.assertEqual(sum_even_numbers([0, 1]), 0)
        self.assertEqual(sum_even_numbers([0, 2]), 2)

    def test_accepts_any_iterable(self):
        self.assertEqual(sum_even_numbers(range(1, 7)), 12)
        self.assertEqual(sum_even_numbers(x for x in [2, 3, 8]), 10)


class TestWholeNumberValues(unittest.TestCase):
    """Real values worth a whole number are accepted and normalised to int."""

    def test_integral_floats(self):
        result = sum_even_numbers([2.0, 3.0, 4.0])
        self.assertEqual(result, 6)
        self.assertIsInstance(result, int)

    def test_fraction_and_decimal(self):
        self.assertEqual(sum_even_numbers([Fraction(4, 2), Decimal("4")]), 6)


class TestInvalidItems(unittest.TestCase):
    """Non-integer items raise by default and are skipped when strict=False."""

    def test_string_item_raises_type_error(self):
        with self.assertRaises(TypeError):
            sum_even_numbers([1, 2, "four"])

    def test_none_item_raises_type_error(self):
        with self.assertRaises(TypeError):
            sum_even_numbers([2, None])

    def test_complex_item_raises_type_error(self):
        with self.assertRaises(TypeError):
            sum_even_numbers([2, 3 + 2j])

    def test_bool_is_not_a_number(self):
        with self.assertRaises(TypeError):
            sum_even_numbers([True, False])

    def test_fractional_float_raises_value_error(self):
        with self.assertRaises(ValueError):
            sum_even_numbers([2, 4.5])

    def test_fractional_decimal_raises_value_error(self):
        with self.assertRaises(ValueError):
            sum_even_numbers([Decimal("4.5")])

    def test_non_finite_raises_value_error(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                sum_even_numbers([2, value])

    def test_error_message_names_the_offending_index(self):
        with self.assertRaises(TypeError) as ctx:
            sum_even_numbers([2, 4, "six"])
        self.assertIn("item 2", str(ctx.exception))
        self.assertIn("'six'", str(ctx.exception))

    def test_non_strict_skips_invalid_items(self):
        self.assertEqual(
            sum_even_numbers([1, "2", 4.5, None, 4, True], strict=False), 4
        )

    def test_non_strict_still_sums_valid_items(self):
        self.assertEqual(sum_even_numbers(["x", 2, 6, "y"], strict=False), 8)


class TestInvalidInput(unittest.TestCase):
    """The argument itself must be a non-string iterable."""

    def test_non_iterable_raises_type_error(self):
        for value in (5, None, 2.5):
            with self.subTest(value=value), self.assertRaises(TypeError):
                sum_even_numbers(value)

    def test_string_input_raises_type_error(self):
        for value in ("24", b"24", bytearray(b"24")):
            with self.subTest(value=value), self.assertRaises(TypeError):
                sum_even_numbers(value)

    def test_input_validation_applies_in_non_strict_mode(self):
        with self.assertRaises(TypeError):
            sum_even_numbers(5, strict=False)


if __name__ == "__main__":
    unittest.main()
