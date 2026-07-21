import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sum_even_numbers import sum_even_numbers


class TestSumEvenNumbers(unittest.TestCase):
    def test_mixed_numbers(self):
        self.assertEqual(sum_even_numbers([1, 2, 3, 4, 5, 6]), 12)

    def test_all_even(self):
        self.assertEqual(sum_even_numbers([2, 4, 6]), 12)

    def test_all_odd(self):
        self.assertEqual(sum_even_numbers([1, 3, 5]), 0)

    def test_empty_list(self):
        self.assertEqual(sum_even_numbers([]), 0)

    def test_negative_numbers(self):
        self.assertEqual(sum_even_numbers([-2, -3, -4]), -6)

    def test_zero_is_even(self):
        self.assertEqual(sum_even_numbers([0, 1]), 0)


if __name__ == "__main__":
    unittest.main()
