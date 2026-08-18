"""Unit tests for sum_even.

Stdlib-only: run with `python -m unittest discover -s tests`.
"""

import sys
import unittest
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

    def test_integral_floats(self):
        self.assertEqual(sum_even_numbers([2.0, 3.0, 4.5]), 2.0)

    def test_accepts_any_iterable(self):
        self.assertEqual(sum_even_numbers(range(1, 7)), 12)
        self.assertEqual(sum_even_numbers(x for x in [2, 3, 8]), 10)

    def test_rejects_non_numbers(self):
        with self.assertRaises(TypeError):
            sum_even_numbers([1, 2, "four"])


if __name__ == "__main__":
    unittest.main()
