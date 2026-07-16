import unittest

from even_sum import sum_even_numbers


class TestSumEvenNumbers(unittest.TestCase):
    def test_mixed_numbers(self):
        self.assertEqual(sum_even_numbers([1, 2, 3, 4, 5, 6]), 12)

    def test_empty_list(self):
        self.assertEqual(sum_even_numbers([]), 0)

    def test_no_evens(self):
        self.assertEqual(sum_even_numbers([1, 3, 5]), 0)

    def test_all_evens(self):
        self.assertEqual(sum_even_numbers([2, 4, 6]), 12)

    def test_negative_numbers(self):
        self.assertEqual(sum_even_numbers([-2, -3, 4]), 2)

    def test_zero_counts_as_even(self):
        self.assertEqual(sum_even_numbers([0, 1, 2]), 2)


if __name__ == "__main__":
    unittest.main()
