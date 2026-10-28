"""Independent plain-Python integer and expression oracles."""
from __future__ import annotations
import ast
import operator
from typing import Mapping


def integer_operator(op: str, a: int, b: int) -> int:
    if isinstance(a, bool) or isinstance(b, bool) or not isinstance(a, int) or not isinstance(b, int):
        raise ValueError("uint8 integer operands required")
    if not 0 <= a <= 255 or not 0 <= b <= 255: raise ValueError("uint8 operands required")
    operations = {"ADD": lambda: (a + b) & 255, "SUB": lambda: (a - b) & 255,
                  "XOR": lambda: a ^ b, "AND": lambda: a & b, "OR": lambda: a | b,
                  "EQ": lambda: int(a == b)}
    try: return operations[op]()
    except KeyError as exc: raise ValueError(f"unknown operator {op!r}") from exc


_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.BitAnd: operator.and_, ast.BitOr: operator.or_, ast.BitXor: operator.xor,
        ast.LShift: operator.lshift, ast.RShift: operator.rshift, ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv}
_UNARY = {ast.USub: operator.neg, ast.UAdd: operator.pos, ast.Invert: operator.invert}
_CMP = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt,
        ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge}


def safe_expression(expression: str, names: Mapping[str, int]) -> int | bool:
    if not isinstance(expression, str) or len(expression) > 1024: raise ValueError("invalid expression")
    try: root = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError) as exc: raise ValueError("invalid expression") from exc
    count = 0

    def walk(node):
        nonlocal count
        count += 1
        if count > 128: raise ValueError("expression too complex")
        if isinstance(node, ast.Expression): return walk(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool): return node.value
            if isinstance(node.value, int) and abs(node.value) <= 2**31: return node.value
            raise ValueError("integer constants only")
        if isinstance(node, ast.Name):
            if node.id not in names: raise ValueError(f"unknown name {node.id!r}")
            value = names[node.id]
            if isinstance(value, bool) or not isinstance(value, int): raise ValueError("integer names only")
            return value
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
            if node.func.id not in {"ADD", "SUB", "XOR", "AND", "OR", "EQ"} or len(node.args) != 2:
                raise ValueError("unsupported canonical operator call")
            return integer_operator(node.func.id, walk(node.args[0]), walk(node.args[1]))
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
            left, right = walk(node.left), walk(node.right)
            if type(node.op) in {ast.LShift, ast.RShift} and not 0 <= right <= 63: raise ValueError("unsafe shift")
            if right == 0 and type(node.op) in {ast.Mod, ast.FloorDiv}: raise ValueError("division by zero")
            value = _BIN[type(node.op)](left, right)
            if isinstance(value, int) and abs(value) > 2**63: raise ValueError("expression result too large")
            return value
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY: return _UNARY[type(node.op)](walk(node.operand))
        if isinstance(node, ast.Compare) and len(node.ops) == len(node.comparators) == 1 and type(node.ops[0]) in _CMP:
            return _CMP[type(node.ops[0])](walk(node.left), walk(node.comparators[0]))
        raise ValueError(f"unsafe expression node {type(node).__name__}")
    return walk(root)


def geometric_product(a, b, signature):
    """Independent dense bitmask-basis geometric product reference."""
    if not isinstance(signature, (list, tuple)) or not 1 <= len(signature) <= 6 \
            or any(metric not in (-1, 1) for metric in signature):
        raise ValueError("signature must contain 1..6 entries of +/-1")
    size = 1 << len(signature)
    if not isinstance(a, (list, tuple)) or not isinstance(b, (list, tuple)) \
            or len(a) != size or len(b) != size:
        raise ValueError("multivector size does not match signature")
    out = [0.0] * size
    for left_mask, left in enumerate(a):
        for right_mask, right in enumerate(b):
            coefficient = float(left) * float(right)
            if coefficient == 0: continue
            sign = 1
            for i in range(len(signature)):
                if left_mask & (1 << i):
                    if (right_mask & ((1 << i) - 1)).bit_count() & 1: sign = -sign
                    if right_mask & (1 << i): sign *= signature[i]
            out[left_mask ^ right_mask] += sign * coefficient
    return out


def geometric_grade(a, grade, signature):
    if isinstance(grade, bool) or not isinstance(grade, int) or not 0 <= grade <= len(signature):
        raise ValueError("invalid grade")
    size = 1 << len(signature)
    if not isinstance(a, (list, tuple)) or len(a) != size: raise ValueError("invalid multivector size")
    return [float(value) if mask.bit_count() == grade else 0.0 for mask, value in enumerate(a)]
