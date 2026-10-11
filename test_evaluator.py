import os
import tempfile
import unittest
from stack_evaluator import (ExpressionError, Stack, evaluate_entries,
                             evaluate_expression, format_number,
                             read_input_file, tokenize, write_output_file)


class TestStack(unittest.TestCase):
    def test_new_stack_is_empty(self):
        s = Stack()
        self.assertTrue(s.is_empty())
        self.assertEqual(s.size(), 0)

    def test_push_then_peek_does_not_remove(self):
        s = Stack()
        s.push(5)
        self.assertEqual(s.peek(), 5)
        self.assertEqual(s.size(), 1)

    def test_lifo_order(self):
        s = Stack()
        for item in (1, 2, 3):
            s.push(item)
        self.assertEqual([s.pop(), s.pop(), s.pop()], [3, 2, 1])
        self.assertTrue(s.is_empty())

    def test_pop_empty_raises(self):
        with self.assertRaises(IndexError):
            Stack().pop()

    def test_peek_empty_raises(self):
        with self.assertRaises(IndexError):
            Stack().peek()


class TestTokenizer(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(tokenize("3 + 5*2"), [3, "+", 5, "*", 2])

    def test_decimals_and_parentheses(self):
        self.assertEqual(tokenize("(1.5+2)"), ["(", 1.5, "+", 2, ")"])

    def test_bad_character(self):
        with self.assertRaises(ExpressionError):
            tokenize("3 $ 4")

    def test_bad_number(self):
        with self.assertRaises(ExpressionError):
            tokenize("1.2.3 + 4")


class TestEvaluation(unittest.TestCase):
    CASES = [
        ("3 + 5 * 2", 13),
        ("(8 / 4) + 7 * 2", 16),
        ("10 - (2 + 3) * 4", -10),
        ("7", 7),
        ("2 + 3", 5),
        ("10 - 4 - 3", 3),
        ("100 / 10 / 5", 2),
        ("2 * (3 + 4) * 5", 70),
        ("((2 + 3) * (4 - 1))", 15),
        ("2 + 3 * 4 - 6 / 2", 11),
        ("-5 + 8", 3),
        ("2 * -3", -6),
        ("3 - -2", 5),
        ("-(2 + 3)", -5),
        ("+4 * 2", 8),
        ("1.5 + 2.5", 4),
        ("7 / 2", 3.5),
        ("   12*   (3+ 1)  ", 48),
    ]

    def test_valid_expressions(self):
        for expression, expected in self.CASES:
            with self.subTest(expression=expression):
                self.assertAlmostEqual(evaluate_expression(expression), expected)

    def test_invalid_expressions(self):
        bad = ["", "   ", "3 +", "* 4", "3 4", "(2 + 3", "2 + 3)", "()", "(2 +) 3",
               "2 (3)", "5 / 0", "5 / (3 - 3)", "2 ** 3", "abc"]
        for expression in bad:
            with self.subTest(expression=expression):
                with self.assertRaises(ExpressionError):
                    evaluate_expression(expression)

    def test_trace_records_every_token(self):
        trace = []
        evaluate_expression("3 + 5 * 2", trace)
        self.assertEqual(trace[0][0], 3)
        self.assertGreaterEqual(len(trace), 5)


class TestFormatting(unittest.TestCase):
    def test_format_number(self):
        self.assertEqual(format_number(13), "13")
        self.assertEqual(format_number(16.0), "16")
        self.assertEqual(format_number(3.5), "3.5")
        self.assertEqual(format_number(1 / 3), "0.333333")
        self.assertEqual(format_number(-0.0), "0")


class TestFiles(unittest.TestCase):
    def test_round_trip_keeps_layout(self):
        text = "3 + 5 * 2\n-----\n(8 / 4) + 7 * 2\n-----\n10 - (2 + 3) * 4\n"
        with tempfile.TemporaryDirectory() as folder:
            src = os.path.join(folder, "input.txt")
            dst = os.path.join(folder, "output.txt")
            with open(src, "w") as f:
                f.write(text)
            write_output_file(dst, evaluate_entries(read_input_file(src)))
            with open(dst) as f:
                self.assertEqual(f.read(), "13\n-----\n16\n-----\n-10\n")

    def test_errors_do_not_stop_the_run(self):
        entries = [("expr", "5 / 0"), ("sep", "-----"), ("expr", "2 + 2")]
        self.assertEqual(evaluate_entries(entries),
                         ["Error: Division by zero", "-----", "4"])

    def test_blank_lines_and_other_separators(self):
        with tempfile.TemporaryDirectory() as folder:
            src = os.path.join(folder, "in.txt")
            with open(src, "w") as f:
                f.write("1 + 1\n\n=====\n2 * 2\n")
            kinds = [k for k, _ in read_input_file(src)]
            self.assertEqual(kinds, ["expr", "blank", "sep", "expr"])


if __name__ == "__main__":
    unittest.main()