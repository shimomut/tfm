"""
Tests for drag gesture detector.

Run with: PYTHONPATH=.:src:ttk pytest test/test_drag_gesture.py -v
"""

import pytest
import time

from tfm_drag_gesture import DragGestureDetector


class TestDragGestureDetector:
    """Test DragGestureDetector class."""
    
    def test_initial_state(self):
        """Test initial state of detector."""
        detector = DragGestureDetector()
        assert not detector.is_dragging()
        assert not detector.state.button_down
    
    def test_button_down_records_position(self):
        """Test that button down records position."""
        detector = DragGestureDetector()
        detector.handle_button_down(100, 200)
        
        assert detector.state.button_down
        assert detector.state.start_x == 100
        assert detector.state.start_y == 200
        assert not detector.state.dragging
    
    def test_small_movement_does_not_trigger_drag(self):
        """Test that small movements don't trigger drag."""
        detector = DragGestureDetector()
        detector.handle_button_down(100, 100)
        
        # Move less than threshold
        result = detector.handle_move(102, 102)
        
        assert not result
        assert not detector.is_dragging()
    
    def test_large_movement_triggers_drag(self):
        """Test that large movements trigger drag."""
        detector = DragGestureDetector()
        detector.handle_button_down(100, 100)
        
        # Move more than threshold (5 pixels)
        result = detector.handle_move(110, 110)
        
        assert result
        assert detector.is_dragging()
    
    def test_move_without_button_down_does_nothing(self):
        """Test that move without button down does nothing."""
        detector = DragGestureDetector()
        
        result = detector.handle_move(100, 100)
        
        assert not result
        assert not detector.is_dragging()
    
    def test_button_up_resets_state(self):
        """Test that button up resets state."""
        detector = DragGestureDetector()
        detector.handle_button_down(100, 100)
        detector.handle_move(110, 110)
        
        was_dragging = detector.handle_button_up()
        
        assert was_dragging
        assert not detector.is_dragging()
        assert not detector.state.button_down
    
    def test_button_up_without_drag_returns_false(self):
        """Test that button up without drag returns false."""
        detector = DragGestureDetector()
        detector.handle_button_down(100, 100)
        
        was_dragging = detector.handle_button_up()
        
        assert not was_dragging
    
    def test_reset_clears_state(self):
        """Test that reset clears all state."""
        detector = DragGestureDetector()
        detector.handle_button_down(100, 100)
        detector.handle_move(110, 110)
        
        detector.reset()
        
        assert not detector.is_dragging()
        assert not detector.state.button_down
        assert detector.state.start_x == 0
        assert detector.state.start_y == 0
    
    def test_drag_threshold_calculation(self):
        """Test that drag threshold is calculated correctly."""
        detector = DragGestureDetector()
        detector.handle_button_down(0, 0)
        
        # Move exactly at threshold (5 pixels)
        # Using Pythagorean theorem: sqrt(3^2 + 4^2) = 5
        result = detector.handle_move(3, 4)
        
        assert result
        assert detector.is_dragging()
