"""
Unit tests for RectangleBatcher and RectBatch classes.

These tests verify the batching logic for combining adjacent cells with the same
background color into single draw calls. The tests use mocking to avoid PyObjC
dependencies and focus on the batching algorithm correctness.
"""

import unittest
from unittest.mock import Mock, MagicMock
from typing import Tuple


# Mock the required modules before importing the backend
import sys
sys.modules['Cocoa'] = MagicMock()
sys.modules['Quartz'] = MagicMock()
sys.modules['objc'] = MagicMock()

# Now we can import the classes we want to test
from ttk.backends.coregraphics_backend import RectBatch, RectangleBatcher


class TestRectBatch(unittest.TestCase):
    """Test cases for RectBatch dataclass."""
    
    def test_rect_batch_creation(self):
        """Test creating a RectBatch with initial values."""
        batch = RectBatch(
            x=10.0,
            y=20.0,
            width=30.0,
            height=40.0,
            bg_rgb=(255, 128, 64)
        )
        
        self.assertEqual(batch.x, 10.0)
        self.assertEqual(batch.y, 20.0)
        self.assertEqual(batch.width, 30.0)
        self.assertEqual(batch.height, 40.0)
        self.assertEqual(batch.bg_rgb, (255, 128, 64))
    
    def test_extend_increases_width(self):
        """Test that extend() increases the batch width."""
        batch = RectBatch(x=0.0, y=0.0, width=10.0, height=20.0, bg_rgb=(0, 0, 0))
        
        batch.extend(5.0)
        self.assertEqual(batch.width, 15.0)
        
        batch.extend(10.0)
        self.assertEqual(batch.width, 25.0)
    
    def test_extend_does_not_change_other_attributes(self):
        """Test that extend() only modifies width."""
        batch = RectBatch(x=5.0, y=10.0, width=15.0, height=20.0, bg_rgb=(255, 0, 0))
        
        batch.extend(10.0)
        
        self.assertEqual(batch.x, 5.0)
        self.assertEqual(batch.y, 10.0)
        self.assertEqual(batch.height, 20.0)
        self.assertEqual(batch.bg_rgb, (255, 0, 0))
    
    def test_right_edge_calculation(self):
        """Test that right_edge() returns x + width."""
        batch = RectBatch(x=10.0, y=0.0, width=25.0, height=20.0, bg_rgb=(0, 0, 0))
        
        self.assertEqual(batch.right_edge(), 35.0)
    
    def test_right_edge_after_extend(self):
        """Test that right_edge() updates after extend()."""
        batch = RectBatch(x=0.0, y=0.0, width=10.0, height=20.0, bg_rgb=(0, 0, 0))
        
        self.assertEqual(batch.right_edge(), 10.0)
        
        batch.extend(15.0)
        self.assertEqual(batch.right_edge(), 25.0)


class TestRectangleBatcher(unittest.TestCase):
    """Test cases for RectangleBatcher class."""
    
    def test_initialization(self):
        """Test that RectangleBatcher initializes with empty state."""
        batcher = RectangleBatcher()
        
        self.assertIsNone(batcher._current_batch)
        self.assertEqual(batcher._batches, [])
    
    def test_add_single_cell_creates_batch(self):
        """Test that adding a single cell creates a new batch."""
        batcher = RectangleBatcher()
        
        batcher.add_cell(0.0, 100.0, 10.0, 20.0, (255, 0, 0))
        
        self.assertIsNotNone(batcher._current_batch)
        self.assertEqual(batcher._current_batch.x, 0.0)
        self.assertEqual(batcher._current_batch.y, 100.0)
        self.assertEqual(batcher._current_batch.width, 10.0)
        self.assertEqual(batcher._current_batch.height, 20.0)
        self.assertEqual(batcher._current_batch.bg_rgb, (255, 0, 0))
    
    def test_add_adjacent_cell_same_color_extends_batch(self):
        """Test that adjacent cells with same color extend the current batch."""
        batcher = RectangleBatcher()
        
        # Add first cell
        batcher.add_cell(0.0, 100.0, 10.0, 20.0, (255, 0, 0))
        
        # Add adjacent cell with same color
        batcher.add_cell(10.0, 100.0, 10.0, 20.0, (255, 0, 0))
        
        # Should still have one batch with extended width
        self.assertEqual(len(batcher._batches), 0)  # Not finished yet
        self.assertIsNotNone(batcher._current_batch)
        self.assertEqual(batcher._current_batch.width, 20.0)
        self.assertEqual(batcher._current_batch.x, 0.0)
    
    def test_add_cell_different_color_creates_new_batch(self):
        """Test that cells with different colors create separate batches."""
        batcher = RectangleBatcher()
        
        # Add first cell (red)
        batcher.add_cell(0.0, 100.0, 10.0, 20.0, (255, 0, 0))
        
        # Add adjacent cell with different color (green)
        batcher.add_cell(10.0, 100.0, 10.0, 20.0, (0, 255, 0))
        
        # Should have finished first batch and started new one
        self.assertEqual(len(batcher._batches), 1)
        self.assertEqual(batcher._batches[0].bg_rgb, (255, 0, 0))
        self.assertEqual(batcher._batches[0].width, 10.0)
        
        self.assertIsNotNone(batcher._current_batch)
        self.assertEqual(batcher._current_batch.bg_rgb, (0, 255, 0))
        self.assertEqual(batcher._current_batch.width, 10.0)
    
    def test_add_cell_different_row_creates_new_batch(self):
        """Test that cells on different rows create separate batches."""
        batcher = RectangleBatcher()
        
        # Add cell on row 1
        batcher.add_cell(0.0, 100.0, 10.0, 20.0, (255, 0, 0))
        
        # Add cell on row 2 (different y)
        batcher.add_cell(0.0, 80.0, 10.0, 20.0, (255, 0, 0))
        
        # Should have finished first batch and started new one
        self.assertEqual(len(batcher._batches), 1)
        self.assertEqual(batcher._batches[0].y, 100.0)
        
        self.assertIsNotNone(batcher._current_batch)
        self.assertEqual(batcher._current_batch.y, 80.0)
    
    def test_add_non_adjacent_cell_creates_new_batch(self):
        """Test that non-adjacent cells create separate batches."""
        batcher = RectangleBatcher()
        
        # Add first cell
        batcher.add_cell(0.0, 100.0, 10.0, 20.0, (255, 0, 0))
        
        # Add non-adjacent cell (gap between them)
        batcher.add_cell(20.0, 100.0, 10.0, 20.0, (255, 0, 0))
        
        # Should have finished first batch and started new one
        self.assertEqual(len(batcher._batches), 1)
        self.assertEqual(batcher._batches[0].x, 0.0)
        self.assertEqual(batcher._batches[0].width, 10.0)
        
        self.assertIsNotNone(batcher._current_batch)
        self.assertEqual(batcher._current_batch.x, 20.0)
    
    def test_finish_row_adds_current_batch(self):
        """Test that finish_row() adds the current batch to the list."""
        batcher = RectangleBatcher()
        
        batcher.add_cell(0.0, 100.0, 10.0, 20.0, (255, 0, 0))
        batcher.finish_row()
        
        self.assertEqual(len(batcher._batches), 1)
        self.assertIsNone(batcher._current_batch)
    
    def test_finish_row_with_no_current_batch(self):
        """Test that finish_row() handles no current batch gracefully."""
        batcher = RectangleBatcher()
        
        batcher.finish_row()  # Should not raise an error
        
        self.assertEqual(len(batcher._batches), 0)
        self.assertIsNone(batcher._current_batch)
    
    def test_get_batches_returns_all_batches(self):
        """Test that get_batches() returns all accumulated batches."""
        batcher = RectangleBatcher()
        
        # Add cells from row 1
        batcher.add_cell(0.0, 100.0, 10.0, 20.0, (255, 0, 0))
        batcher.add_cell(10.0, 100.0, 10.0, 20.0, (255, 0, 0))
        batcher.finish_row()
        
        # Add cells from row 2
        batcher.add_cell(0.0, 80.0, 10.0, 20.0, (0, 255, 0))
        batcher.finish_row()
        
        batches = batcher.get_batches()
        
        self.assertEqual(len(batches), 2)
        self.assertEqual(batches[0].width, 20.0)  # Extended batch
        self.assertEqual(batches[0].bg_rgb, (255, 0, 0))
        self.assertEqual(batches[1].width, 10.0)
        self.assertEqual(batches[1].bg_rgb, (0, 255, 0))
    
    def test_get_batches_finishes_current_batch(self):
        """Test that get_batches() finishes the current batch if exists."""
        batcher = RectangleBatcher()
        
        batcher.add_cell(0.0, 100.0, 10.0, 20.0, (255, 0, 0))
        # Don't call finish_row()
        
        batches = batcher.get_batches()
        
        self.assertEqual(len(batches), 1)
        self.assertIsNone(batcher._current_batch)
    
    def test_get_batches_resets_batcher(self):
        """Test that get_batches() resets the batcher state."""
        batcher = RectangleBatcher()
        
        batcher.add_cell(0.0, 100.0, 10.0, 20.0, (255, 0, 0))
        batcher.finish_row()
        
        batches = batcher.get_batches()
        self.assertEqual(len(batches), 1)
        
        # Batcher should be reset
        self.assertEqual(len(batcher._batches), 0)
        self.assertIsNone(batcher._current_batch)
    
    def test_multiple_adjacent_cells_extend_batch(self):
        """Test that multiple adjacent cells with same color extend the batch."""
        batcher = RectangleBatcher()
        
        # Add 5 adjacent cells with same color
        for i in range(5):
            batcher.add_cell(i * 10.0, 100.0, 10.0, 20.0, (255, 0, 0))
        
        batcher.finish_row()
        batches = batcher.get_batches()
        
        self.assertEqual(len(batches), 1)
        self.assertEqual(batches[0].width, 50.0)  # 5 cells * 10.0 width
        self.assertEqual(batches[0].x, 0.0)
    
    def test_alternating_colors_create_multiple_batches(self):
        """Test that alternating colors create multiple batches."""
        batcher = RectangleBatcher()
        
        # Add cells with alternating colors
        batcher.add_cell(0.0, 100.0, 10.0, 20.0, (255, 0, 0))    # Red
        batcher.add_cell(10.0, 100.0, 10.0, 20.0, (0, 255, 0))   # Green
        batcher.add_cell(20.0, 100.0, 10.0, 20.0, (255, 0, 0))   # Red
        batcher.add_cell(30.0, 100.0, 10.0, 20.0, (0, 255, 0))   # Green
        
        batcher.finish_row()
        batches = batcher.get_batches()
        
        self.assertEqual(len(batches), 4)
        self.assertEqual(batches[0].bg_rgb, (255, 0, 0))
        self.assertEqual(batches[1].bg_rgb, (0, 255, 0))
        self.assertEqual(batches[2].bg_rgb, (255, 0, 0))
        self.assertEqual(batches[3].bg_rgb, (0, 255, 0))
    
    def test_can_extend_batch_with_no_current_batch(self):
        """Test that _can_extend_batch returns False when no current batch."""
        batcher = RectangleBatcher()
        
        result = batcher._can_extend_batch(0.0, 100.0, (255, 0, 0))
        
        self.assertFalse(result)
    
    def test_can_extend_batch_with_matching_criteria(self):
        """Test that _can_extend_batch returns True for matching cells."""
        batcher = RectangleBatcher()
        
        batcher.add_cell(0.0, 100.0, 10.0, 20.0, (255, 0, 0))
        
        # Adjacent cell, same row, same color
        result = batcher._can_extend_batch(10.0, 100.0, (255, 0, 0))
        
        self.assertTrue(result)
    
    def test_can_extend_batch_with_different_color(self):
        """Test that _can_extend_batch returns False for different color."""
        batcher = RectangleBatcher()
        
        batcher.add_cell(0.0, 100.0, 10.0, 20.0, (255, 0, 0))
        
        # Adjacent cell, same row, different color
        result = batcher._can_extend_batch(10.0, 100.0, (0, 255, 0))
        
        self.assertFalse(result)
    
    def test_can_extend_batch_with_different_row(self):
        """Test that _can_extend_batch returns False for different row."""
        batcher = RectangleBatcher()
        
        batcher.add_cell(0.0, 100.0, 10.0, 20.0, (255, 0, 0))
        
        # Adjacent x, different row, same color
        result = batcher._can_extend_batch(10.0, 80.0, (255, 0, 0))
        
        self.assertFalse(result)
    
    def test_can_extend_batch_with_non_adjacent_position(self):
        """Test that _can_extend_batch returns False for non-adjacent position."""
        batcher = RectangleBatcher()
        
        batcher.add_cell(0.0, 100.0, 10.0, 20.0, (255, 0, 0))
        
        # Non-adjacent x, same row, same color
        result = batcher._can_extend_batch(20.0, 100.0, (255, 0, 0))
        
        self.assertFalse(result)
    
    def test_floating_point_adjacency_tolerance(self):
        """Test that adjacency check handles floating-point precision."""
        batcher = RectangleBatcher()
        
        batcher.add_cell(0.0, 100.0, 10.0, 20.0, (255, 0, 0))
        
        # Slightly off due to floating-point precision (within 0.1 epsilon)
        result = batcher._can_extend_batch(10.05, 100.0, (255, 0, 0))
        
        self.assertTrue(result)
    
    def test_complex_row_batching_scenario(self):
        """Test a complex scenario with multiple color changes in a row."""
        batcher = RectangleBatcher()
        
        # Row with pattern: RRR GG RRR B
        colors = [
            (255, 0, 0), (255, 0, 0), (255, 0, 0),  # 3 red
            (0, 255, 0), (0, 255, 0),                # 2 green
            (255, 0, 0), (255, 0, 0), (255, 0, 0),  # 3 red
            (0, 0, 255)                               # 1 blue
        ]
        
        for i, color in enumerate(colors):
            batcher.add_cell(i * 10.0, 100.0, 10.0, 20.0, color)
        
        batcher.finish_row()
        batches = batcher.get_batches()
        
        # Should create 4 batches: RRR, GG, RRR, B
        self.assertEqual(len(batches), 4)
        self.assertEqual(batches[0].width, 30.0)  # 3 red cells
        self.assertEqual(batches[1].width, 20.0)  # 2 green cells
        self.assertEqual(batches[2].width, 30.0)  # 3 red cells
        self.assertEqual(batches[3].width, 10.0)  # 1 blue cell


if __name__ == '__main__':
    unittest.main()
