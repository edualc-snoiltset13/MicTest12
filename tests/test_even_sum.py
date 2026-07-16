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

    def test_float_raises_type_error(self):
        with self.assertRaises(TypeError) as ctx:
            sum_even_numbers([1, 2.5, 3])
        self.assertIn("index 1", str(ctx.exception))

    def test_string_raises_type_error(self):
        with self.assertRaises(TypeError):
            sum_even_numbers([2, "4"])

    def test_none_raises_type_error(self):
        with self.assertRaises(TypeError):
            sum_even_numbers([None])

    def test_bool_raises_type_error(self):
        with self.assertRaises(TypeError):
            sum_even_numbers([True, 2])


if __name__ == "__main__":
    unittest.main()
