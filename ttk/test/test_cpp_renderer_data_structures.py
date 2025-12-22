#!/usr/bin/env python3
"""
Test data structures for C++ renderer parsing functions.
This demonstrates the expected input format for parse_grid() and parse_color_pairs().
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def create_test_grid(rows=3, cols=5):
    """
    Create a test grid with the expected format:
    List of lists containing (char, color_pair, attributes) tuples.
    
    Returns:
        grid: List[List[Tuple[str, int, int]]]
    """
    grid = []
    for row in range(rows):
        row_cells = []
        for col in range(cols):
            # Create a simple pattern
            if col == 0:
                char = ' '
                color_pair = 0
                attributes = 0
            elif row == 0:
                char = chr(ord('A') + col - 1)
                color_pair = 1
                attributes = 0  # Normal
            elif row == 1:
                char = chr(ord('a') + col - 1)
                color_pair = 2
                attributes = 1  # BOLD
            else:
                char = str(col)
                color_pair = 3
                attributes = 2  # UNDERLINE
            
            row_cells.append((char, color_pair, attributes))
        grid.append(row_cells)
    
    return grid

def create_test_color_pairs():
    """
    Create test color pairs with the expected format:
    Dict mapping color_pair ID to ((r,g,b), (r,g,b)) tuples.
    
    Returns:
        color_pairs: Dict[int, Tuple[Tuple[int, int, int], Tuple[int, int, int]]]
    """
    color_pairs = {
        0: ((255, 255, 255), (0, 0, 0)),      # White on black
        1: ((0, 255, 0), (0, 0, 0)),          # Green on black
        2: ((255, 0, 0), (255, 255, 255)),    # Red on white
        3: ((0, 0, 255), (128, 128, 128)),    # Blue on gray
    }
    return color_pairs

def create_test_grid_with_utf8():
    """Create a test grid with UTF-8 characters (Japanese, emoji, etc.)."""
    grid = [
        [('H', 0, 0), ('e', 0, 0), ('l', 0, 0), ('l', 0, 0), ('o', 0, 0)],
        [('こ', 1, 0), ('ん', 1, 0), ('に', 1, 0), ('ち', 1, 0), ('は', 1, 0)],
        [('😀', 2, 0), ('🎉', 2, 0), ('✓', 2, 0), ('→', 2, 0), ('★', 2, 0)],
    ]
    return grid

def validate_grid_format(grid, expected_rows, expected_cols):
    """Validate that a grid has the correct format."""
    print(f"\nValidating grid format (expected {expected_rows}x{expected_cols}):")
    
    # Check it's a list
    if not isinstance(grid, list):
        print(f"  ✗ Grid is not a list: {type(grid)}")
        return False
    print(f"  ✓ Grid is a list")
    
    # Check number of rows
    if len(grid) != expected_rows:
        print(f"  ✗ Grid has {len(grid)} rows, expected {expected_rows}")
        return False
    print(f"  ✓ Grid has {expected_rows} rows")
    
    # Check each row
    for row_idx, row in enumerate(grid):
        if not isinstance(row, list):
            print(f"  ✗ Row {row_idx} is not a list: {type(row)}")
            return False
        
        if len(row) != expected_cols:
            print(f"  ✗ Row {row_idx} has {len(row)} columns, expected {expected_cols}")
            return False
        
        # Check each cell
        for col_idx, cell in enumerate(row):
            if not isinstance(cell, tuple):
                print(f"  ✗ Cell ({row_idx}, {col_idx}) is not a tuple: {type(cell)}")
                return False
            
            if len(cell) != 3:
                print(f"  ✗ Cell ({row_idx}, {col_idx}) has {len(cell)} elements, expected 3")
                return False
            
            char, color_pair, attributes = cell
            
            if not isinstance(char, str):
                print(f"  ✗ Cell ({row_idx}, {col_idx}) char is not a string: {type(char)}")
                return False
            
            if not isinstance(color_pair, int):
                print(f"  ✗ Cell ({row_idx}, {col_idx}) color_pair is not an int: {type(color_pair)}")
                return False
            
            if not isinstance(attributes, int):
                print(f"  ✗ Cell ({row_idx}, {col_idx}) attributes is not an int: {type(attributes)}")
                return False
    
    print(f"  ✓ All {expected_rows * expected_cols} cells have correct format")
    return True

def validate_color_pairs_format(color_pairs):
    """Validate that color_pairs has the correct format."""
    print("\nValidating color_pairs format:")
    
    # Check it's a dict
    if not isinstance(color_pairs, dict):
        print(f"  ✗ color_pairs is not a dict: {type(color_pairs)}")
        return False
    print(f"  ✓ color_pairs is a dict")
    
    # Check each entry
    for pair_id, colors in color_pairs.items():
        if not isinstance(pair_id, int):
            print(f"  ✗ Color pair ID {pair_id} is not an int: {type(pair_id)}")
            return False
        
        if not isinstance(colors, tuple) or len(colors) != 2:
            print(f"  ✗ Color pair {pair_id} value is not a 2-tuple: {colors}")
            return False
        
        fg, bg = colors
        
        for color_name, color in [("foreground", fg), ("background", bg)]:
            if not isinstance(color, tuple) or len(color) != 3:
                print(f"  ✗ Color pair {pair_id} {color_name} is not an RGB tuple: {color}")
                return False
            
            r, g, b = color
            for component_name, component in [("R", r), ("G", g), ("B", b)]:
                if not isinstance(component, int):
                    print(f"  ✗ Color pair {pair_id} {color_name} {component_name} is not an int: {type(component)}")
                    return False
                
                if component < 0 or component > 255:
                    print(f"  ✗ Color pair {pair_id} {color_name} {component_name} out of range: {component}")
                    return False
    
    print(f"  ✓ All {len(color_pairs)} color pairs have correct format")
    return True

def main():
    """Run validation tests."""
    print("=" * 60)
    print("C++ Renderer Data Structure Format Validation")
    print("=" * 60)
    
    all_passed = True
    
    # Test basic grid
    print("\n1. Testing basic ASCII grid:")
    grid = create_test_grid(3, 5)
    if not validate_grid_format(grid, 3, 5):
        all_passed = False
    else:
        print(f"  Sample cell: {grid[0][1]}")
    
    # Test UTF-8 grid
    print("\n2. Testing UTF-8 grid:")
    utf8_grid = create_test_grid_with_utf8()
    if not validate_grid_format(utf8_grid, 3, 5):
        all_passed = False
    else:
        print(f"  Sample UTF-8 cells: {utf8_grid[1][0]}, {utf8_grid[2][0]}")
    
    # Test color pairs
    print("\n3. Testing color pairs:")
    color_pairs = create_test_color_pairs()
    if not validate_color_pairs_format(color_pairs):
        all_passed = False
    else:
        print(f"  Sample color pair: {color_pairs[1]}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All data structure formats are valid!")
        print("\nThese data structures can be passed to the C++ parsing functions:")
        print("  - parse_grid(grid, rows, cols)")
        print("  - parse_color_pairs(color_pairs)")
    else:
        print("✗ Some validation tests failed")
        sys.exit(1)
    print("=" * 60)

if __name__ == '__main__':
    main()
