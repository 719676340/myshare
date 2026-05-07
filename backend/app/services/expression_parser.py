"""AST-based expression parser and evaluator for custom indicator formulas.

Safely parses user-defined indicator expressions (e.g., VOL/MA(VOL,20))
using Python's ast module. Validates against a whitelist of allowed
fields, functions, and node types to prevent code injection.
"""

import ast
import pandas as pd

# D-02: Safe field name mapping (uppercase alias -> DataFrame column name)
SAFE_FIELDS = {
    "OPEN": "open",
    "HIGH": "high",
    "LOW": "low",
    "CLOSE": "close",
    "VOL": "vol",
    "AMOUNT": "amount",
    "PRE_CLOSE": "pre_close",
    "CHANGE_PCT": "change_pct",
}

# D-03: Safe functions with pandas-based implementations
SAFE_FUNCTIONS = {
    "MA": lambda series, period: series.rolling(
        window=int(period), min_periods=1
    ).mean(),
    "EMA": lambda series, period: series.ewm(
        span=int(period), adjust=False
    ).mean(),
    "STD": lambda series, period: series.rolling(
        window=int(period), min_periods=1
    ).std(),
    "MAX": lambda series, period: series.rolling(
        window=int(period), min_periods=1
    ).max(),
    "MIN": lambda series, period: series.rolling(
        window=int(period), min_periods=1
    ).min(),
    "REF": lambda series, n: series.shift(int(n)),
    "CROSS": lambda a, b: (a.shift(1) <= b.shift(1)) & (a > b),
}

# D-01: Allowed AST node types whitelist
SAFE_NODE_TYPES = {
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Call,
    ast.Name,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.UAdd,
    ast.USub,
    ast.Load,
}

# Combined set of all allowed names (fields + functions)
_ALLOWED_NAMES = set(SAFE_FIELDS.keys()) | set(SAFE_FUNCTIONS.keys())


def parse_and_validate(expr_str: str) -> tuple:
    """Parse and validate an expression string against the safety whitelist.

    Args:
        expr_str: The expression string to parse (e.g., "VOL/MA(VOL,20)").

    Returns:
        Tuple of (validated AST tree, list of used field names).

    Raises:
        SyntaxError: If the expression has syntax errors.
        ValueError: If the expression uses disallowed operations or unknown names.
    """
    try:
        tree = ast.parse(expr_str, mode="eval")
    except SyntaxError as e:
        raise SyntaxError(f"Invalid expression syntax: {e}") from e

    used_fields = []

    for node in ast.walk(tree):
        # Validate node type
        if type(node) not in SAFE_NODE_TYPES:
            raise ValueError(
                f"Disallowed operation in expression: {type(node).__name__}"
            )

        # Validate Name nodes
        if isinstance(node, ast.Name):
            name = node.id
            if name not in _ALLOWED_NAMES:
                raise ValueError(
                    f"Unknown name in expression: '{name}'. "
                    f"Allowed: {sorted(_ALLOWED_NAMES)}"
                )
            # Track field usage (not function names)
            if name in SAFE_FIELDS and name not in used_fields:
                used_fields.append(name)

        # Validate Call nodes
        if isinstance(node, ast.Call):
            # Must call a named function (not attribute access)
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only named function calls are allowed")
            func_name = node.func.id
            if func_name not in SAFE_FUNCTIONS:
                raise ValueError(f"Unknown function: '{func_name}'")
            # All safe functions require exactly 2 arguments
            if len(node.args) != 2:
                raise ValueError(
                    f"Function '{func_name}' requires exactly 2 arguments, "
                    f"got {len(node.args)}"
                )
            # Reject keyword arguments
            if node.keywords:
                raise ValueError("Keyword arguments are not allowed")

    return (tree, used_fields)


def evaluate_expression(tree, df: pd.DataFrame) -> pd.Series:
    """Evaluate a validated expression tree against a DataFrame.

    Args:
        tree: Validated AST expression tree from parse_and_validate.
        df: DataFrame with OHLCV columns.

    Returns:
        pandas Series with the computed values.
    """
    namespace = {"__builtins__": {}}

    # Add safe fields mapped to DataFrame columns
    for alias, col_name in SAFE_FIELDS.items():
        if col_name in df.columns:
            namespace[alias] = df[col_name]

    # Add safe functions
    namespace.update(SAFE_FUNCTIONS)

    result = eval(compile(tree, "<expr>", "eval"), namespace)
    return result


def evaluate_expression_with_custom(
    tree, df: pd.DataFrame, custom_indicators: dict
) -> pd.Series:
    """Evaluate a validated expression with additional custom indicator series.

    Same as evaluate_expression but adds custom_indicators to the namespace,
    enabling cross-indicator references like EMA(MACD_DIF, 9).

    Args:
        tree: Validated AST expression tree from parse_and_validate.
        df: DataFrame with OHLCV columns.
        custom_indicators: Dict of {name: pd.Series} for already-computed indicators.

    Returns:
        pandas Series with the computed values.
    """
    namespace = {"__builtins__": {}}

    # Add safe fields mapped to DataFrame columns
    for alias, col_name in SAFE_FIELDS.items():
        if col_name in df.columns:
            namespace[alias] = df[col_name]

    # Add safe functions
    namespace.update(SAFE_FUNCTIONS)

    # Add custom indicator series
    namespace.update(custom_indicators)

    result = eval(compile(tree, "<expr>", "eval"), namespace)
    return result
