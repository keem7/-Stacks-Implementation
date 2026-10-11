import argparse
import re
import sys


class Stack:
    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        if self.is_empty():
            raise IndexError("pop from an empty stack")
        return self._items.pop()

    def peek(self):
        if self.is_empty():
            raise IndexError("peek at an empty stack")
        return self._items[-1]

    def is_empty(self):
        return len(self._items) == 0

    def size(self):
        return len(self._items)

    def to_list(self):
        return list(self._items)

    def __len__(self):
        return len(self._items)

    def __repr__(self):
        return f"Stack({self._items})"


class ExpressionError(Exception):
    pass


PRECEDENCE = {"+": 1, "-": 1, "*": 2, "/": 2, "neg": 3}
BINARY_OPERATORS = ("+", "-", "*", "/")
DIGITS = "0123456789"


def tokenize(expression):
    tokens = []
    i, n = 0, len(expression)
    while i < n:
        ch = expression[i]
        if ch.isspace():
            i += 1
        elif ch in DIGITS or ch == ".":
            j, dots = i, 0
            while j < n and (expression[j] in DIGITS or expression[j] == "."):
                dots += expression[j] == "."
                j += 1
            text = expression[i:j]
            if dots > 1 or text == ".":
                raise ExpressionError(f"Invalid number '{text}'")
            tokens.append(float(text) if dots else int(text))
            i = j
        elif ch in BINARY_OPERATORS or ch in "()":
            tokens.append(ch)
            i += 1
        else:
            raise ExpressionError(f"Unexpected character '{ch}'")
    return tokens


def apply_operator(operators, values):
    op = operators.pop()
    try:
        if op == "neg":
            values.push(-values.pop())
            return
        right = values.pop()
        left = values.pop()
    except IndexError:
        raise ExpressionError("Malformed expression (missing operand)")
    if op == "+":
        values.push(left + right)
    elif op == "-":
        values.push(left - right)
    elif op == "*":
        values.push(left * right)
    elif op == "/":
        if right == 0:
            raise ExpressionError("Division by zero")
        values.push(left / right)


def evaluate_expression(expression, trace=None):
    tokens = tokenize(expression)
    if not tokens:
        raise ExpressionError("Empty expression")
    values = Stack()
    operators = Stack()
    expect_operand = True
    for tok in tokens:
        if isinstance(tok, (int, float)):
            if not expect_operand:
                raise ExpressionError("Missing operator between two operands")
            values.push(tok)
            expect_operand = False
        elif tok == "(":
            if not expect_operand:
                raise ExpressionError("Missing operator before '('")
            operators.push("(")
        elif tok == ")":
            if expect_operand:
                raise ExpressionError("Missing operand before ')'")
            while not operators.is_empty() and operators.peek() != "(":
                apply_operator(operators, values)
            if operators.is_empty():
                raise ExpressionError("Mismatched parentheses (extra ')')")
            operators.pop()
        else:
            if expect_operand:
                if tok == "-":
                    operators.push("neg")
                elif tok != "+":
                    raise ExpressionError(
                        f"Operator '{tok}' has no left operand")
            else:
                while (not operators.is_empty()
                       and operators.peek() != "("
                       and PRECEDENCE[operators.peek()] >= PRECEDENCE[tok]):
                    apply_operator(operators, values)
                operators.push(tok)
                expect_operand = True
        if trace is not None:
            trace.append((tok, values.to_list(), operators.to_list()))
    if expect_operand:
        raise ExpressionError("Expression is incomplete (ends with an operator)")
    while not operators.is_empty():
        if operators.peek() == "(":
            raise ExpressionError("Mismatched parentheses (missing ')')")
        apply_operator(operators, values)
        if trace is not None:
            trace.append(("<end>", values.to_list(), operators.to_list()))
    result = values.pop()
    if not values.is_empty():
        raise ExpressionError("Malformed expression")
    return result


def format_number(value):
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        text = f"{value:.6f}".rstrip("0").rstrip(".")
        return "0" if text in ("", "-0") else text
    return str(value)


SEPARATOR_RE = re.compile(r"^\s*([-=_*#~])\1{2,}\s*$")


def read_input_file(path):
    entries = []
    with open(path, "r", encoding="utf-8-sig") as handle:
        for raw in handle:
            line = raw.rstrip("\r\n")
            if line.strip() == "":
                entries.append(("blank", ""))
            elif SEPARATOR_RE.match(line):
                entries.append(("sep", line.strip()))
            else:
                entries.append(("expr", line.strip()))
    return entries


def evaluate_entries(entries):
    results = []
    for kind, text in entries:
        if kind == "expr":
            try:
                results.append(format_number(evaluate_expression(text)))
            except ExpressionError as error:
                results.append(f"Error: {error}")
        else:
            results.append(text)
    return results


def write_output_file(path, lines):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for line in lines:
            handle.write(line + "\n")


def print_trace(expression):
    trace = []
    try:
        evaluate_expression(expression, trace)
    except ExpressionError as error:
        print(f"  (trace stopped: {error})")
    print(f"  {'token':<8}{'value stack':<26}operator stack")
    for tok, vals, ops in trace:
        print(f"  {str(tok):<8}{str(vals):<26}{ops}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Evaluate expressions from a file using stacks.")
    parser.add_argument("input", nargs="?", default="input.txt")
    parser.add_argument("output", nargs="?", default="output.txt")
    parser.add_argument("--trace", action="store_true",
                        help="print the stack contents after every token")
    args = parser.parse_args(argv)
    try:
        entries = read_input_file(args.input)
    except FileNotFoundError:
        print(f"Error: input file '{args.input}' was not found.")
        return 1
    except OSError as error:
        print(f"Error: cannot read '{args.input}': {error}")
        return 1
    results = evaluate_entries(entries)
    for (kind, text), result in zip(entries, results):
        if kind == "expr":
            print(f"{text}  =  {result}")
            if args.trace:
                print_trace(text)
    try:
        write_output_file(args.output, results)
    except OSError as error:
        print(f"Error: cannot write '{args.output}': {error}")
        return 1
    print(f"\nDone. Results written to '{args.output}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())