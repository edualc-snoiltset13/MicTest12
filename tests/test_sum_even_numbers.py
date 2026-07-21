import unittest

from sum_even_numbers import sum_even_numbers


class TestSumEvenNumbers(unittest.TestCase):
    def test_mixed_numbers(self):
        self.assertEqual(sum_even_numbers([1, 2, 3, 4, 5, 6]), 12)

    def test_all_even(self):
        self.assertEqual(sum_even_numbers([2, 4, 6, 8]), 20)

    def test_all_odd(self):
        self.assertEqual(sum_even_numbers([1, 3, 5, 7]), 0)

    def test_empty_list(self):
        self.assertEqual(sum_even_numbers([]), 0)

    def test_negative_numbers(self):
        self.assertEqual(sum_even_numbers([-2, -3, -4, 5]), -6)

    def test_zero_is_even(self):
        self.assertEqual(sum_even_numbers([0, 1, 2]), 2)

    def test_integral_floats_counted(self):
        self.assertEqual(sum_even_numbers([2.0, 3.0, 4.0]), 6)

    def test_non_integral_floats_skipped(self):
        self.assertEqual(sum_even_numbers([2.5, 4, 1.5]), 4)


if __name__ == "__main__":
    unittest.main()
