import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sum_even_numbers import sum_even_numbers


class TestSumEvenNumbers(unittest.TestCase):
    def test_mixed_list(self):
        self.assertEqual(sum_even_numbers([1, 2, 3, 4, 5, 6]), 12)

    def test_empty_list(self):
        self.assertEqual(sum_even_numbers([]), 0)

    def test_no_evens(self):
        self.assertEqual(sum_even_numbers([1, 3, 5, 7]), 0)

    def test_all_evens(self):
        self.assertEqual(sum_even_numbers([2, 4, 6]), 12)

    def test_negative_numbers(self):
        self.assertEqual(sum_even_numbers([-2, -3, -4, 5]), -6)

    def test_zero_is_even(self):
        self.assertEqual(sum_even_numbers([0, 1, 2]), 2)

    def test_whole_floats_count(self):
        self.assertEqual(sum_even_numbers([2.0, 3.0, 4.5]), 2)

    def test_generator_input(self):
        self.assertEqual(sum_even_numbers(range(1, 11)), 30)


if __name__ == "__main__":
    unittest.main()
