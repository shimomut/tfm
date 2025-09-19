#!/usr/bin/env python3
"""
Test file for syntax highlighting in TFM text viewer
"""

import os
import sys
from pathlib import Path

def hello_world():
    """A simple function to test syntax highlighting"""
    message = "Hello, World!"
    print(f"Message: {message}")
    
    # Test various Python constructs
    numbers = [1, 2, 3, 4, 5]
    squares = [x**2 for x in numbers]
    
    for i, square in enumerate(squares):
        print(f"Square of {i+1} is {square}")
    
    return True

class TestClass:
    """A test class"""
    
    def __init__(self, name):
        self.name = name
        self._private = "secret"
    
    def get_name(self):
        return self.name
    
    @property
    def private_value(self):
        return self._private

if __name__ == "__main__":
    # Test the functionality
    test = TestClass("TFM Text Viewer")
    print(f"Class name: {test.get_name()}")
    
    if hello_world():
        print("✅ Syntax highlighting test complete!")
    else:
        print("❌ Test failed")