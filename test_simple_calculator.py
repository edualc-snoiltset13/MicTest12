"""
Tests for simple_calculator: the Calculator class plus the REPL command
processor that exposes memory and history.

Run:
    python -m unittest test_simple_calculator
"""

import unittest

from simple_calculator import Calculator, process_command, _QUIT


class ArithmeticTests(unittest.TestCase):
    def setUp(self):
        self.calc = Calculator()

    def test_basic_ops(self):
        self.assertEqual(self.calc.add(2, 3), 5)
        self.assertEqual(self.calc.subtract(10, 4), 6)
        self.assertEqual(self.calc.multiply(6, 7), 42)
        self.assertEqual(self.calc.divide(20, 4), 5)
        self.assertEqual(self.calc.power(2, 8), 256)
        self.assertEqual(self.calc.modulo(10, 3), 1)

    def test_divide_by_zero(self):
        with self.assertRaises(ValueError):
            self.calc.divide(1, 0)

    def test_modulo_by_zero(self):
        with self.assertRaises(ValueError):
            self.calc.modulo(1, 0)

    def test_history_records_each_op(self):
        self.calc.add(1, 2)
        self.calc.multiply(3, 4)
        self.assertEqual(len(self.calc.history), 2)
        self.assertEqual(self.calc.history[-1]["result"], 12)


class ProcessCommandTests(unittest.TestCase):
    def setUp(self):
        self.calc = Calculator()

    def test_arithmetic(self):
        self.assertEqual(process_command(self.calc, "3 + 4"), "7.0")
        self.assertEqual(process_command(self.calc, "10 / 4"), "2.5")

    def test_quit_sentinels(self):
        for line in ("quit", "exit", "", "   "):
            self.assertIs(process_command(self.calc, line), _QUIT)

    def test_bad_expression(self):
        self.assertTrue(process_command(self.calc, "3 +").startswith("error:"))
        self.assertTrue(process_command(self.calc, "3 ? 4").startswith("error:"))

    def test_divide_by_zero_message(self):
        self.assertEqual(process_command(self.calc, "1 / 0"), "error: division by zero")

    def test_store_and_recall(self):
        process_command(self.calc, "2 + 3")
        self.assertEqual(process_command(self.calc, "store"), "stored 5.0 in memory")
        self.assertEqual(process_command(self.calc, "recall"), "5.0")

    def test_store_with_no_history(self):
        self.assertEqual(process_command(self.calc, "store"), "error: no result to store")

    def test_mem_as_operand(self):
        process_command(self.calc, "10 + 5")
        process_command(self.calc, "store")  # memory = 15.0
        self.assertEqual(process_command(self.calc, "mem + 5"), "20.0")
        self.assertEqual(process_command(self.calc, "2 * mem"), "30.0")

    def test_clearmem(self):
        process_command(self.calc, "1 + 1")
        process_command(self.calc, "store")
        self.assertEqual(process_command(self.calc, "clearmem"), "memory cleared")
        self.assertEqual(process_command(self.calc, "recall"), "0")

    def test_history_command(self):
        self.assertEqual(process_command(self.calc, "history"), "(history empty)")
        process_command(self.calc, "2 + 3")
        out = process_command(self.calc, "history")
        self.assertIn("2.0 add 3.0 = 5.0", out)

    def test_clearhist(self):
        process_command(self.calc, "2 + 3")
        self.assertEqual(process_command(self.calc, "clearhist"), "history cleared")
        self.assertEqual(process_command(self.calc, "history"), "(history empty)")

    def test_help(self):
        self.assertIn("commands:", process_command(self.calc, "help"))

    def test_commands_are_case_insensitive(self):
        process_command(self.calc, "1 + 1")
        self.assertEqual(process_command(self.calc, "STORE"), "stored 2.0 in memory")
        self.assertEqual(process_command(self.calc, "Recall"), "2.0")


if __name__ == "__main__":
    unittest.main(verbosity=2)
