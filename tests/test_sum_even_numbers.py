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

    def test_whole_floats_count_partial_ones_do_not(self):
        self.assertEqual(sum_even_numbers([2.0, 4.5, 3.0]), 2.0)

    def test_accepts_any_iterable(self):
        self.assertEqual(sum_even_numbers(range(1, 7)), 12)

    def test_booleans_rejected(self):
        with self.assertRaises(TypeError):
            sum_even_numbers([True, 2])

    def test_non_numbers_rejected(self):
        with self.assertRaises(TypeError):
            sum_even_numbers([1, "2"])


if __name__ == "__main__":
    unittest.main()
