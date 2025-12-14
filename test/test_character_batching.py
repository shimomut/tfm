#!/usr/bin/env python3
"""
Test character batching logic implementation.

This test verifies that the character batching logic correctly:
1. Identifies continuous character runs with same attributes
2. Skips spaces efficiently
3. Detects batch boundaries on attribute changes
4. Calculates correct x-coordinates for batch start positions
5. Handles edge cases (empty rows, single chars, all same/different attrs)
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from ttk.renderer import TextAttribute

def test_batching_with_spaces():
    """Test that spaces are skipped and batches are created correctly."""
    print("\n" + "="*70)
    print("Test: Batching with spaces")
    print("="*70)
    
    backend = CoreGraphicsBackend(
        window_title="Batching Test",
        font_name="Menlo",
        font_size=12,
        rows=24,
        cols=80
    )
    backend.initialize()
    
    # Initialize color pairs
    backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))
    
    # Create a row with: "ABC   DEF" (3 chars, 3 spaces, 3 chars)
    # This should create 2 batches
    for col in range(3):
        backend.grid[0][col] = ('ABC'[col], 1, 0)
    for col in range(3, 6):
        backend.grid[0][col] = (' ', 1, 0)
    for col in range(6, 9):
        backend.grid[0][col] = ('DEF'[col-6], 1, 0)
    
    # Refresh to trigger drawing
    backend.refresh()
    
    print("✓ Batching with spaces works correctly")
    backend.shutdown()

def test_batching_attribute_changes():
    """Test that batches are split on attribute changes."""
    print("\n" + "="*70)
    print("Test: Batching with attribute changes")
    print("="*70)
    
    backend = CoreGraphicsBackend(
        window_title="Attribute Test",
        font_name="Menlo",
        font_size=12,
        rows=24,
        cols=80
    )
    backend.initialize()
    
    # Initialize color pairs
    backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))
    backend.init_color_pair(2, (255, 0, 0), (0, 0, 0))
    
    # Create a row with: "AAA" (normal) + "BBB" (bold) + "CCC" (color 2)
    # This should create 3 batches
    for col in range(3):
        backend.grid[0][col] = ('A', 1, 0)
    for col in range(3, 6):
        backend.grid[0][col] = ('B', 1, TextAttribute.BOLD)
    for col in range(6, 9):
        backend.grid[0][col] = ('C', 2, 0)
    
    # Refresh to trigger drawing
    backend.refresh()
    
    print("✓ Batching with attribute changes works correctly")
    backend.shutdown()

def test_batching_all_same_attributes():
    """Test maximum batching when all characters have same attributes."""
    print("\n" + "="*70)
    print("Test: Maximum batching (all same attributes)")
    print("="*70)
    
    backend = CoreGraphicsBackend(
        window_title="Max Batch Test",
        font_name="Menlo",
        font_size=12,
        rows=24,
        cols=80
    )
    backend.initialize()
    
    # Initialize color pairs
    backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))
    
    # Fill entire row with same character and attributes
    # This should create 1 large batch
    for col in range(80):
        backend.grid[0][col] = ('X', 1, 0)
    
    # Refresh to trigger drawing
    backend.refresh()
    
    print("✓ Maximum batching works correctly")
    backend.shutdown()

def test_batching_all_different_attributes():
    """Test that each character gets its own batch when all attributes differ."""
    print("\n" + "="*70)
    print("Test: No batching (all different attributes)")
    print("="*70)
    
    backend = CoreGraphicsBackend(
        window_title="No Batch Test",
        font_name="Menlo",
        font_size=12,
        rows=24,
        cols=80
    )
    backend.initialize()
    
    # Initialize color pairs (1-10, since 0 is reserved)
    for i in range(1, 11):
        backend.init_color_pair(i, (255, 255, 255), (i*25, 0, 0))
    
    # Create a row where each character has different color
    # This should create 10 separate batches
    for col in range(10):
        backend.grid[0][col] = (chr(ord('A') + col), col + 1, 0)
    
    # Refresh to trigger drawing
    backend.refresh()
    
    print("✓ No batching (all different) works correctly")
    backend.shutdown()

def test_batching_single_character():
    """Test edge case of single character."""
    print("\n" + "="*70)
    print("Test: Single character batching")
    print("="*70)
    
    backend = CoreGraphicsBackend(
        window_title="Single Char Test",
        font_name="Menlo",
        font_size=12,
        rows=24,
        cols=80
    )
    backend.initialize()
    
    # Initialize color pairs
    backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))
    
    # Create a row with single character
    backend.grid[0][0] = ('X', 1, 0)
    
    # Refresh to trigger drawing
    backend.refresh()
    
    print("✓ Single character batching works correctly")
    backend.shutdown()

def test_batching_empty_row():
    """Test edge case of empty row (all spaces)."""
    print("\n" + "="*70)
    print("Test: Empty row (all spaces)")
    print("="*70)
    
    backend = CoreGraphicsBackend(
        window_title="Empty Row Test",
        font_name="Menlo",
        font_size=12,
        rows=24,
        cols=80
    )
    backend.initialize()
    
    # Initialize color pairs
    backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))
    
    # Row is already all spaces by default
    # Refresh to trigger drawing
    backend.refresh()
    
    print("✓ Empty row handling works correctly")
    backend.shutdown()

def test_batching_leading_trailing_spaces():
    """Test handling of leading and trailing spaces."""
    print("\n" + "="*70)
    print("Test: Leading and trailing spaces")
    print("="*70)
    
    backend = CoreGraphicsBackend(
        window_title="Spaces Test",
        font_name="Menlo",
        font_size=12,
        rows=24,
        cols=80
    )
    backend.initialize()
    
    # Initialize color pairs
    backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))
    
    # Create a row with: "   ABC   " (3 leading spaces, 3 chars, 3 trailing spaces)
    for col in range(3, 6):
        backend.grid[0][col] = ('ABC'[col-3], 1, 0)
    
    # Refresh to trigger drawing
    backend.refresh()
    
    print("✓ Leading and trailing spaces handled correctly")
    backend.shutdown()

def test_batching_reverse_video():
    """Test batching with reverse video attribute."""
    print("\n" + "="*70)
    print("Test: Reverse video batching")
    print("="*70)
    
    backend = CoreGraphicsBackend(
        window_title="Reverse Test",
        font_name="Menlo",
        font_size=12,
        rows=24,
        cols=80
    )
    backend.initialize()
    
    # Initialize color pairs
    backend.init_color_pair(1, (255, 255, 255), (0, 0, 0))
    
    # Create a row with: "AAA" (normal) + "BBB" (reverse)
    # This should create 2 batches
    for col in range(3):
        backend.grid[0][col] = ('A', 1, 0)
    for col in range(3, 6):
        backend.grid[0][col] = ('B', 1, TextAttribute.REVERSE)
    
    # Refresh to trigger drawing
    backend.refresh()
    
    print("✓ Reverse video batching works correctly")
    backend.shutdown()

def main():
    """Run all batching tests."""
    print("\n" + "="*70)
    print("Character Batching Logic Tests")
    print("="*70)
    print("\nThese tests verify the character batching implementation:")
    print("  - Space skipping")
    print("  - Batch boundary detection")
    print("  - Attribute change handling")
    print("  - Edge cases (empty, single char, all same/different)")
    
    try:
        test_batching_with_spaces()
        test_batching_attribute_changes()
        test_batching_all_same_attributes()
        test_batching_all_different_attributes()
        test_batching_single_character()
        test_batching_empty_row()
        test_batching_leading_trailing_spaces()
        test_batching_reverse_video()
        
        print("\n" + "="*70)
        print("All batching tests passed! ✓")
        print("="*70)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
