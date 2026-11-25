"""Safe arithmetic for a calculation specialist."""

import ast
import operator
from langchain import tools
from langchain_core.tools import tool

# Only these arithmetic operations are accepted from the model's expression.
OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
       ast.Mod: operator.mod, ast.Pow: operator.pow,
       ast.UAdd: operator.pos, ast.USub: operator.neg}


def _eval(node):
    """Evaluate permitted parts of an expression without running Python code."""
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        if abs(node.value) > 1e12:
            raise ValueError("Number is too large")
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
        return OPS[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 12:
            raise ValueError("Exponent is too large")
        result = OPS[type(node.op)](left, right)
        if abs(result) > 1e18:
            raise ValueError("Result is too large")
        return result
    raise ValueError("Only arithmetic numbers and operators are allowed")


@tool
def calculate(expression: str) -> str:
    """Calculate basic arithmetic and return the expression with its result."""
    try:
        if len(expression) > 200:
            raise ValueError("Expression is too long")
        return f"{expression} = {_eval(ast.parse(expression, mode='eval'))}"
    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError) as exc:
        return f"Calculation failed: {exc}"


def noncommuting_elements(question: str) -> str | None:
    """Solve requests for the sorted elements in a Markdown table's counterexamples."""
    language = question.casefold()
    if not all(phrase in language for phrase in (
        "not commutative", "comma separated", "alphabetical", "subset",
    )):
        return None

    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in question.splitlines()
        if line.strip().startswith("|") and line.strip().endswith("|")
    ]
    if len(rows) < 3:
        return None
    labels = rows[0][1:]
    separator, *data = rows[1:]
    width = len(labels) + 1
    if len(labels) != len(set(labels)) or len(data) != len(labels):
        return None
    if len(separator) != width or any(
        not cell.strip(":") or set(cell.strip(":")) != {"-"} for cell in separator
    ):
        return None
    if any(len(row) != width for row in data):
        return None
    if {row[0] for row in data} != set(labels):
        return None

    table = {row[0]: dict(zip(labels, row[1:])) for row in data}
    if any(value not in table for row in table.values() for value in row.values()):
        return None
    involved = {
        left for left in labels
        if any(table[left][right] != table[right][left] for right in labels)
    }
    return ", ".join(sorted(involved, key=str.casefold)) if involved else None


@tool
def count_albums(
    albums: list[dict],
    start_year: int,
    end_year: int
) -> int:
    """Count albums released between start_year and end_year (inclusive)."""
    album_count = 0
    seen = set()
    for loop in albums:
        year = loop.get("year")
        if year is not None and start_year <= year <= end_year and loop.get("title", "years") not in seen:
            album_count += 1
            seen.add(loop.get("title", "years"))
    return album_count

