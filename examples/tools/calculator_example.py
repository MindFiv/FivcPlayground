"""
Calculator Tool Example

This example demonstrates how to use the built-in calculator tool for various
mathematical operations. The calculator tool supports multiple modes:
    - eval: Evaluate mathematical expressions
    - add, subtract, multiply, divide: Basic arithmetic operations
    - power: Exponentiation
    - sqrt: Square root
    - factorial: Factorial calculation

Usage:
    python examples/tools/calculator_example.py
"""

from fivcadvisor.tools.calculator import calculator


def main():
    """
    Run the calculator tool example.
    """

    print("FivcAdvisor - Calculator Tool Example")
    print("\n" + "=" * 60)

    # Example 1: Evaluate mathematical expressions
    print("\n1. Evaluate Mathematical Expressions (eval mode)")
    print("-" * 60)
    expressions = [
        "2 + 3 * 4",
        "sqrt(16) + 2",
        "pow(2, 3) + 5",
        "sin(0) + cos(0)",
        "log(10) + exp(1)",
    ]
    for expr in expressions:
        result = calculator(mode="eval", expression=expr)
        print(f"  {expr:20} = {result}")

    # Example 2: Basic arithmetic operations
    print("\n2. Basic Arithmetic Operations")
    print("-" * 60)
    operations = [
        ("add", {"a": 10, "b": 5}, "10 + 5"),
        ("subtract", {"a": 20, "b": 8}, "20 - 8"),
        ("multiply", {"a": 6, "b": 7}, "6 * 7"),
        ("divide", {"a": 20, "b": 4}, "20 / 4"),
    ]
    for mode, kwargs, description in operations:
        result = calculator(mode=mode, **kwargs)
        print(f"  {description:20} = {result}")

    # Example 3: Advanced operations
    print("\n3. Advanced Operations")
    print("-" * 60)
    advanced = [
        ("power", {"a": 2, "b": 8}, "2 ^ 8"),
        ("sqrt", {"a": 25}, "sqrt(25)"),
        ("factorial", {"a": 5}, "5!"),
        ("sqrt", {"a": 2}, "sqrt(2)"),
    ]
    for mode, kwargs, description in advanced:
        result = calculator(mode=mode, **kwargs)
        print(f"  {description:20} = {result}")

    # Example 4: Error handling
    print("\n4. Error Handling")
    print("-" * 60)
    error_cases = [
        ("divide", {"a": 10, "b": 0}, "Division by zero"),
        ("sqrt", {"a": -1}, "Square root of negative"),
        ("factorial", {"a": -1}, "Negative factorial"),
        ("eval", {"expression": ""}, "Empty expression"),
    ]
    for mode, kwargs, description in error_cases:
        result = calculator(mode=mode, **kwargs)
        print(f"  {description:20} -> {result}")

    # Example 5: Using with agents
    print("\n5. Using Calculator with Agents")
    print("-" * 60)
    print("  The calculator tool can be used with FivcAdvisor agents:")
    print("  - Agents automatically select calculator for math queries")
    print("  - Supports both simple and complex expressions")
    print("  - Provides safe evaluation with limited namespace")
    print("  - Handles errors gracefully")

    print("\n" + "=" * 60)
    print("✓ Calculator tool example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

