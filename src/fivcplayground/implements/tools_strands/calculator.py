"""
Calculator tool implementation for Strands framework.

This module provides a calculator tool using the Strands framework, implementing
the ITool interface for integration with the FivcPlayground component architecture.

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
import logging
from typing import Literal, Union, Any

from strands.tools import tool as make_tool
from strands.types.tools import ToolResult
from uuid import uuid4

from fivcplayground.interfaces import ITool

logger = logging.getLogger(__name__)


@make_tool
def _calculator_impl(
    mode: Literal[
        "eval", "add", "subtract", "multiply", "divide", "power", "sqrt", "factorial"
    ] = "eval",
    expression: str = "",
    a: Union[int, float] = 0,
    b: Union[int, float] = 0,
) -> ToolResult:
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
        a: First number for binary operations or input for unary operations
        b: Second number for binary operations

    Returns:
        ToolResult with calculation result or error message
    """
    try:
        if mode == "eval":
            if not expression:
                return ToolResult(
                    content=[
                        {
                            "type": "text",
                            "text": "Error: expression is required for 'eval' mode",
                        }
                    ],
                    status="error",
                    toolUseId=str(uuid4()),
                )
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
            return ToolResult(
                content=[{"type": "text", "text": str(result)}],
                status="success",
                toolUseId=str(uuid4()),
            )
        elif mode == "add":
            result = a + b
        elif mode == "subtract":
            result = a - b
        elif mode == "multiply":
            result = a * b
        elif mode == "divide":
            if b == 0:
                return ToolResult(
                    content=[{"type": "text", "text": "Error: Division by zero"}],
                    status="error",
                    toolUseId=str(uuid4()),
                )
            result = a / b
        elif mode == "power":
            result = a**b
        elif mode == "sqrt":
            if a < 0:
                return ToolResult(
                    content=[
                        {
                            "type": "text",
                            "text": "Error: Cannot calculate square root of negative number",
                        }
                    ],
                    status="error",
                    toolUseId=str(uuid4()),
                )
            result = math.sqrt(a)
        elif mode == "factorial":
            if not isinstance(a, int) or a < 0:
                return ToolResult(
                    content=[
                        {
                            "type": "text",
                            "text": "Error: Factorial requires non-negative integer",
                        }
                    ],
                    status="error",
                    toolUseId=str(uuid4()),
                )
            result = math.factorial(a)
        else:
            return ToolResult(
                content=[{"type": "text", "text": f"Error: Unknown mode '{mode}'"}],
                status="error",
                toolUseId=str(uuid4()),
            )

        return ToolResult(
            content=[{"type": "text", "text": str(result)}],
            status="success",
            toolUseId=str(uuid4()),
        )
    except Exception as e:
        return ToolResult(
            content=[{"type": "text", "text": f"Error: {str(e)}"}],
            status="error",
            toolUseId=str(uuid4()),
        )


class CalculatorToolImpl(ITool):
    """
    Implementation of ITool interface for calculator tool using Strands framework.

    This class wraps the Strands calculator tool and provides the ITool interface
    for integration with FivcPlayground's component architecture.
    """

    def __init__(self):
        """Initialize the calculator tool."""
        self._name = "calculator"
        self._description = "Perform mathematical calculations in various modes (eval, add, subtract, multiply, divide, power, sqrt, factorial)"
        self._underlying = _calculator_impl

    @property
    def name(self) -> str:
        """Get the name of the tool."""
        return self._name

    @property
    def description(self) -> str:
        """Get the description of the tool."""
        return self._description

    def get_underlying(self) -> Any:
        """Get the underlying Strands tool object."""
        return self._underlying
