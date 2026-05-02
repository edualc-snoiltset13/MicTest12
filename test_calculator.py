import unittest
from calculator import add, subtract, multiply, divide, power, modulo, calculate


class TestBasicArithmetic(unittest.TestCase):

    def test_add(self):
        self.assertEqual(add(2, 3), 5)
        self.assertEqual(add(0, 0), 0)
        self.assertEqual(add(-1, 1), 0)

    def test_subtract(self):
        self.assertEqual(subtract(10, 4), 6)
        self.assertEqual(subtract(0, 0), 0)
        self.assertEqual(subtract(5, 8), -3)

    def test_multiply(self):
        self.assertEqual(multiply(3, 7), 21)
        self.assertEqual(multiply(0, 100), 0)
        self.assertEqual(multiply(-2, 3), -6)

    def test_divide(self):
        self.assertEqual(divide(8, 2), 4.0)
        self.assertEqual(divide(7, 2), 3.5)
        self.assertEqual(divide(-9, 3), -3.0)

    def test_power(self):
        self.assertEqual(power(2, 3), 8)
        self.assertEqual(power(5, 0), 1)
        self.assertEqual(power(10, 1), 10)

    def test_modulo(self):
        self.assertEqual(modulo(10, 3), 1)
        self.assertEqual(modulo(8, 4), 0)
        self.assertEqual(modulo(7, 2), 1)

    def test_calculate_dispatch(self):
        self.assertEqual(calculate(2, "+", 3), 5)
        self.assertEqual(calculate(10, "-", 4), 6)
        self.assertEqual(calculate(3, "*", 7), 21)
        self.assertEqual(calculate(8, "/", 2), 4.0)
        self.assertEqual(calculate(2, "**", 3), 8)
        self.assertEqual(calculate(10, "%", 3), 1)


if __name__ == "__main__":
    unittest.main()
