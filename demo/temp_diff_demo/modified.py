#!/usr/bin/env python3
"""
Modified Python Script - Enhanced Version
"""

def calculate_sum(a, b):
    """Calculate sum of two numbers"""
    result = a + b
    return result

def calculate_difference(a, b):
    """Calculate difference of two numbers"""
    return a - b

def calculate_product(a, b):
    """Calculate product of two numbers"""
    return a * b

def main():
    x = 10
    y = 20
    z = 5
    print(f"Sum: {calculate_sum(x, y)}")
    print(f"Difference: {calculate_difference(x, z)}")
    print(f"Product: {calculate_product(x, y)}")

if __name__ == '__main__':
    main()
