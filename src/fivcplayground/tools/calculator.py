"""
Calculator tool for mathematical operations.

This module provides a unified calculator tool for performing various mathematical
operations. The tool is implemented using LangChain's @tool decorator for seamless
integration with agents.

The calculator tool supports multiple modes:
    - "eval": Evaluate a mathematical expression
    - "add": Add numbers
    - "subtract": Subtract numbers
    - "multiply": Multiply numbers
    - "divide": Divide numbers
    - "power": Raise to power
    - "sqrt": Square root
    - "factorial": Factorial calculation
"""

import math
from typing import Literal, Union


def calculator(
    mode: Literal[
        "eval", "add", "subtract", "multiply", "divide", "power", "sqrt", "factorial"
    ] = "eval",
    expression: str = "",
    a: Union[int, float] = 0,
    b: Union[int, float] = 0,
) -> str:
    """
    Perform mathematical calculations in various modes.

    Args:
        mode: Operation mode (default: "eval")
            - "eval": Evaluate a mathematical expression (e.g., "2 + 3 * 4")
            - "add": Add two numbers (requires a and b)
            - "subtract": Subtract b from a (requires a and b)
            - "multiply": Multiply two numbers (requires a and b)
            - "divide": Divide a by b (requires a and b)
            - "power": Raise a to power b (requires a and b)
            - "sqrt": Calculate square root of a (requires a)
            - "factorial": Calculate factorial of a (requires a)

        expression: Mathematical expression for "eval" mode
            Examples: "2 + 3", "10 * 5", "2 ** 3", "sqrt(16)"

        a: First number for binary operations or input for unary operations

        b: Second number for binary operations

    Returns:
        Calculation result as string or error message

    Examples:
        >>> calculator(mode="eval", expression="2 + 3 * 4")
        '14'
        >>> calculator(mode="add", a=10, b=5)
        '15'
        >>> calculator(mode="multiply", a=6, b=7)
        '42'
        >>> calculator(mode="sqrt", a=16)
        '4.0'
        >>> calculator(mode="factorial", a=5)
        '120'
    """
    try:
        if mode == "eval":
            if not expression:
                return "Error: expression is required for 'eval' mode"
            # Safe evaluation with limited namespace
            safe_dict = {
                "sqrt": math.sqrt,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "log": math.log,
                "log10": math.log10,
                "exp": math.exp,
                "pi": math.pi,
                "e": math.e,
                "abs": abs,
                "pow": pow,
                "round": round,
            }
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            return str(result)

        elif mode == "add":
            result = a + b
            return str(result)

        elif mode == "subtract":
            result = a - b
            return str(result)

        elif mode == "multiply":
            result = a * b
            return str(result)

        elif mode == "divide":
            if b == 0:
                return "Error: Division by zero"
            result = a / b
            return str(result)

        elif mode == "power":
            result = a**b
            return str(result)

        elif mode == "sqrt":
            if a < 0:
                return "Error: Cannot calculate square root of negative number"
            result = math.sqrt(a)
            return str(result)

        elif mode == "factorial":
            if not isinstance(a, int) or a < 0:
                return "Error: Factorial requires non-negative integer"
            result = math.factorial(a)
            return str(result)

        else:
            return f"Error: Unknown mode '{mode}'. Valid modes: eval, add, subtract, multiply, divide, power, sqrt, factorial"

    except ZeroDivisionError:
        return "Error: Division by zero"
    except ValueError as e:
        return f"Error: Invalid input. {str(e)}"
    except SyntaxError as e:
        return f"Error: Invalid expression syntax. {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
