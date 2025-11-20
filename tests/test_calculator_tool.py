#!/usr/bin/env python3
"""
Tests for the calculator tool.
"""

import pytest
from fivcplayground.tools.calculator import calculator


class TestCalculatorTool:
    """Tests for the calculator tool"""

    def test_eval_addition(self):
        """Test basic addition in eval mode"""
        result = calculator(mode="eval", expression="2 + 3")
        assert result == "5"

    def test_eval_subtraction(self):
        """Test basic subtraction in eval mode"""
        result = calculator(mode="eval", expression="10 - 4")
        assert result == "6"

    def test_eval_multiplication(self):
        """Test basic multiplication in eval mode"""
        result = calculator(mode="eval", expression="3 * 4")
        assert result == "12"

    def test_eval_division(self):
        """Test basic division in eval mode"""
        result = calculator(mode="eval", expression="10 / 2")
        assert result == "5.0"

    def test_eval_division_with_float(self):
        """Test division resulting in float"""
        result = calculator(mode="eval", expression="7 / 2")
        assert float(result) == 3.5

    def test_eval_power(self):
        """Test exponentiation in eval mode"""
        result = calculator(mode="eval", expression="2 ** 3")
        assert result == "8"

    def test_eval_complex_expression(self):
        """Test complex expression with multiple operations"""
        result = calculator(mode="eval", expression="2 + 3 * 4")
        assert result == "14"  # 3 * 4 = 12, 2 + 12 = 14

    def test_eval_parentheses(self):
        """Test expression with parentheses"""
        result = calculator(mode="eval", expression="(2 + 3) * 4")
        assert result == "20"

    def test_eval_negative_numbers(self):
        """Test with negative numbers"""
        result = calculator(mode="eval", expression="-5 + 3")
        assert result == "-2"

    def test_eval_decimal_numbers(self):
        """Test with decimal numbers"""
        result = calculator(mode="eval", expression="3.5 + 2.5")
        assert result == "6.0"

    def test_eval_invalid_expression(self):
        """Test that invalid expression returns error message"""
        result = calculator(mode="eval", expression="2 +")
        assert "error" in result.lower() or "invalid" in result.lower()

    def test_eval_division_by_zero(self):
        """Test division by zero handling"""
        result = calculator(mode="eval", expression="5 / 0")
        assert "error" in result.lower() or "zero" in result.lower()

    def test_eval_empty_expression(self):
        """Test empty expression"""
        result = calculator(mode="eval", expression="")
        assert "error" in result.lower() or "required" in result.lower()

    def test_add_mode(self):
        """Test add mode"""
        result = calculator(mode="add", a=10, b=5)
        assert result == "15"

    def test_subtract_mode(self):
        """Test subtract mode"""
        result = calculator(mode="subtract", a=10, b=3)
        assert result == "7"

    def test_multiply_mode(self):
        """Test multiply mode"""
        result = calculator(mode="multiply", a=6, b=7)
        assert result == "42"

    def test_divide_mode(self):
        """Test divide mode"""
        result = calculator(mode="divide", a=10, b=2)
        assert result == "5.0"

    def test_power_mode(self):
        """Test power mode"""
        result = calculator(mode="power", a=2, b=3)
        assert result == "8"

    def test_sqrt_mode(self):
        """Test sqrt mode"""
        result = calculator(mode="sqrt", a=16)
        assert result == "4.0"

    def test_factorial_mode(self):
        """Test factorial mode"""
        result = calculator(mode="factorial", a=5)
        assert result == "120"

    def test_sqrt_negative_error(self):
        """Test sqrt with negative number"""
        result = calculator(mode="sqrt", a=-4)
        assert "error" in result.lower()

    def test_factorial_negative_error(self):
        """Test factorial with negative number"""
        result = calculator(mode="factorial", a=-5)
        assert "error" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
