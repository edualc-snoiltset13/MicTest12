"""Unit tests for int_list.

Stdlib-only: run with `python -m unittest discover -s tests`.
"""

import sys
import unittest
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

# Make the project root importable when run from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from int_list import (  # noqa: E402
    coerce_int,
    filter_int_list,
    is_int_list,
    validate_int_list,
)


class CoerceIntTests(unittest.TestCase):
    def test_returns_ints_unchanged(self):
        self.assertEqual(coerce_int(0), 0)
        self.assertEqual(coerce_int(-7), -7)
        self.assertEqual(coerce_int(10 ** 30), 10 ** 30)

    def test_accepts_whole_valued_reals(self):
        cases = [(4.0, 4), (-4.0, -4), (Fraction(4, 2), 2), (Decimal("4"), 4)]
        for item, expected in cases:
            with self.subTest(item=item):
                self.assertEqual(coerce_int(item), expected)
                self.assertIsInstance(coerce_int(item), int)

    def test_rejects_non_numbers(self):
        for item in ("2", b"2", None, [1], {}, object(), 1 + 2j):
            with self.subTest(item=item):
                with self.assertRaises(TypeError):
                    coerce_int(item)

    def test_rejects_bools(self):
        for item in (True, False):
            with self.subTest(item=item):
                with self.assertRaises(TypeError):
                    coerce_int(item)

    def test_rejects_fractional_values(self):
        for item in (2.5, -0.5, Fraction(1, 3), Decimal("2.5")):
            with self.subTest(item=item):
                with self.assertRaises(ValueError):
                    coerce_int(item)

    def test_rejects_non_finite_values(self):
        for item in (float("nan"), float("inf"), float("-inf"), Decimal("NaN")):
            with self.subTest(item=item):
                with self.assertRaises(ValueError):
                    coerce_int(item)

    def test_error_names_type_and_value(self):
        with self.assertRaises(TypeError) as ctx:
            coerce_int("2")
        self.assertIn("str", str(ctx.exception))
        self.assertIn("'2'", str(ctx.exception))


class ValidateIntListTests(unittest.TestCase):
    def test_returns_new_list_of_ints(self):
        values = [1, 2, 3]
        result = validate_int_list(values)
        self.assertEqual(result, [1, 2, 3])
        self.assertIsNot(result, values)

    def test_normalises_whole_valued_reals(self):
        result = validate_int_list([1, 2.0, Fraction(6, 2), Decimal("4")])
        self.assertEqual(result, [1, 2, 3, 4])
        self.assertTrue(all(isinstance(v, int) for v in result))

    def test_accepts_any_iterable(self):
        self.assertEqual(validate_int_list((1, 2)), [1, 2])
        self.assertEqual(validate_int_list(range(3)), [0, 1, 2])
        self.assertEqual(validate_int_list(iter([4, 5])), [4, 5])

    def test_empty_list_allowed_by_default(self):
        self.assertEqual(validate_int_list([]), [])

    def test_empty_list_rejected_when_disallowed(self):
        with self.assertRaises(ValueError) as ctx:
            validate_int_list([], allow_empty=False)
        self.assertIn("empty", str(ctx.exception))

    def test_rejects_non_integer_items(self):
        for values in ([1, "2"], [None], [1, [2]], [True], [{}]):
            with self.subTest(values=values):
                with self.assertRaises(TypeError):
                    validate_int_list(values)

    def test_rejects_fractional_and_non_finite_items(self):
        for values in ([1, 2.5], [float("nan")], [float("inf")]):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    validate_int_list(values)

    def test_rejects_string_and_bytes_containers(self):
        for values in ("123", b"123", bytearray(b"123")):
            with self.subTest(values=values):
                with self.assertRaises(TypeError):
                    validate_int_list(values)

    def test_rejects_non_iterable_container(self):
        for values in (5, None, object()):
            with self.subTest(values=values):
                with self.assertRaises(TypeError):
                    validate_int_list(values)

    def test_error_reports_offending_index(self):
        with self.assertRaises(TypeError) as ctx:
            validate_int_list([1, 2, "three"])
        self.assertIn("values[2]", str(ctx.exception))

    def test_error_uses_supplied_name(self):
        with self.assertRaises(TypeError) as ctx:
            validate_int_list([1, "2"], name="numbers")
        self.assertIn("numbers[1]", str(ctx.exception))

    def test_reports_first_bad_item_only(self):
        with self.assertRaises(TypeError) as ctx:
            validate_int_list(["a", "b"])
        message = str(ctx.exception)
        self.assertIn("values[0]", message)
        self.assertNotIn("values[1]", message)

    def test_does_not_chain_the_inner_error(self):
        with self.assertRaises(TypeError) as ctx:
            validate_int_list([1, "2"])
        self.assertIsNone(ctx.exception.__cause__)


class FilterIntListTests(unittest.TestCase):
    def test_splits_integers_from_the_rest(self):
        integers, rejected = filter_int_list([1, "2", 3.5, 4])
        self.assertEqual(integers, [1, 4])
        self.assertEqual(rejected, [(1, "2"), (2, 3.5)])

    def test_all_valid_leaves_nothing_rejected(self):
        integers, rejected = filter_int_list([1, 2.0, Decimal("3")])
        self.assertEqual(integers, [1, 2, 3])
        self.assertEqual(rejected, [])

    def test_all_invalid_leaves_no_integers(self):
        integers, rejected = filter_int_list([None, "x", True])
        self.assertEqual(integers, [])
        self.assertEqual(rejected, [(0, None), (1, "x"), (2, True)])

    def test_empty_list_yields_two_empty_lists(self):
        self.assertEqual(filter_int_list([]), ([], []))

    def test_still_rejects_a_bad_container(self):
        for values in ("123", 5, None):
            with self.subTest(values=values):
                with self.assertRaises(TypeError):
                    filter_int_list(values)


class IsIntListTests(unittest.TestCase):
    def test_true_for_lists_of_integers(self):
        self.assertTrue(is_int_list([1, 2, 3]))
        self.assertTrue(is_int_list([1, 2.0, Decimal("3")]))
        self.assertTrue(is_int_list([]))

    def test_false_for_lists_with_non_integers(self):
        self.assertFalse(is_int_list([1, "2"]))
        self.assertFalse(is_int_list([1, 2.5]))
        self.assertFalse(is_int_list([True]))

    def test_false_for_bad_containers(self):
        self.assertFalse(is_int_list("123"))
        self.assertFalse(is_int_list(None))
        self.assertFalse(is_int_list(5))

    def test_allow_empty_flag_is_honoured(self):
        self.assertFalse(is_int_list([], allow_empty=False))
        self.assertTrue(is_int_list([1], allow_empty=False))


if __name__ == "__main__":
    unittest.main()
