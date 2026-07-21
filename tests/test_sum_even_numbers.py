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

    def test_float_raises_type_error(self):
        with self.assertRaises(TypeError):
            sum_even_numbers([2, 4.0, 6])

    def test_string_raises_type_error(self):
        with self.assertRaises(TypeError):
            sum_even_numbers([1, "2", 3])

    def test_none_element_raises_type_error(self):
        with self.assertRaises(TypeError):
            sum_even_numbers([2, None])

    def test_bool_raises_type_error(self):
        with self.assertRaises(TypeError):
            sum_even_numbers([True, 2])

    def test_non_iterable_raises_type_error(self):
        with self.assertRaises(TypeError):
            sum_even_numbers(42)

    def test_error_message_includes_index_and_type(self):
        with self.assertRaisesRegex(TypeError, "index 1.*str"):
            sum_even_numbers([2, "x"])


if __name__ == "__main__":
    unittest.main()
