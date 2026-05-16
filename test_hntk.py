import unittest


class HntkTest(unittest.TestCase):
    def test_truthy(self):
        self.assertTrue(True)

    def test_equal(self):
        self.assertEqual(1 + 1, 2)

    def test_string(self):
        self.assertEqual("hntk".upper(), "HNTK")

    def test_list(self):
        self.assertEqual(sorted([3, 1, 2]), [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
