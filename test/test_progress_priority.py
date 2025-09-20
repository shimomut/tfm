#!/usr/bin/env python3
"""
Test that progress display takes priority over quick choice bar
"""

import sys
import os
from unittest.mock import Mock

# Add the src directory to the path so we can import TFM modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_progress_manager import ProgressManager, OperationType


class MockQuickChoiceBar:
    """Mock quick choice bar"""
    def __init__(self):
        self.mode = False
        self.draw_called = False
    
    def draw(self, stdscr, safe_addstr, status_y, width):
        self.draw_called = True


class MockTFM:
    """Mock TFM class to test status drawing priority"""
    
    def __init__(self):
        self.progress_manager = ProgressManager()
        self.quick_choice_bar = MockQuickChoiceBar()
        self.stdscr = Mock()
        self.isearch_mode = False
        self.status_draws = []
        
    def get_current_pane(self):
        return {}
    
    def safe_addstr(self, y, x, text, attr=None):
        """Mock safe_addstr that records what's drawn"""
        self.status_draws.append(f"({y},{x}): {text}")
    
    def draw_status(self):
        """Simplified version of draw_status method to test priority"""
        height, width = 25, 80  # Mock screen size
        status_y = height - 1
        
        # Reset tracking
        self.status_draws = []
        self.quick_choice_bar.draw_called = False
        
        # Progress display takes precedence over everything else during operations
        if self.progress_manager.is_operation_active():
            # Fill entire status line with background color
            status_line = " " * (width - 1)
            self.safe_addstr(status_y, 0, status_line)
            
            # Get formatted progress text from progress manager
            progress_text = self.progress_manager.get_progress_text(width - 4)
            
            # Draw progress text
            self.safe_addstr(status_y, 2, progress_text)
            return

        # If in quick choice mode, show quick choice bar
        if self.quick_choice_bar.mode:
            self.quick_choice_bar.draw(self.stdscr, self.safe_addstr, status_y, width)
            return


def test_progress_takes_priority():
    """Test that progress display takes priority over quick choice bar"""
    print("Testing progress display priority...")
    
    tfm = MockTFM()
    
    # Test 1: Quick choice bar active, no progress
    tfm.quick_choice_bar.mode = True
    tfm.draw_status()
    
    assert tfm.quick_choice_bar.draw_called, "Quick choice bar should be drawn when no progress active"
    assert len(tfm.status_draws) == 0, "No progress text should be drawn"
    
    # Test 2: Both quick choice bar and progress active - progress should win
    tfm.progress_manager.start_operation(OperationType.DELETE, 10, "", None)
    tfm.progress_manager.update_progress("test_file.txt", 5)
    
    tfm.quick_choice_bar.mode = True  # Still active
    tfm.draw_status()
    
    assert not tfm.quick_choice_bar.draw_called, "Quick choice bar should NOT be drawn when progress is active"
    assert len(tfm.status_draws) > 0, "Progress text should be drawn"
    
    # Check that progress text contains expected content
    progress_text = " ".join([draw.split(": ", 1)[1] for draw in tfm.status_draws if ": " in draw])
    assert "Deleting" in progress_text, f"Should contain 'Deleting', got: {progress_text}"
    assert "5/10" in progress_text, f"Should contain '5/10', got: {progress_text}"
    assert "test_file.txt" in progress_text, f"Should contain 'test_file.txt', got: {progress_text}"
    
    # Test 3: Progress finished, quick choice bar should work again
    tfm.progress_manager.finish_operation()
    tfm.quick_choice_bar.mode = True
    tfm.draw_status()
    
    assert tfm.quick_choice_bar.draw_called, "Quick choice bar should be drawn again after progress finishes"
    
    print("✅ Progress priority test passed!")


def test_progress_without_quick_choice():
    """Test that progress works normally when quick choice bar is not active"""
    print("\nTesting progress without quick choice interference...")
    
    tfm = MockTFM()
    
    # Start progress operation
    tfm.progress_manager.start_operation(OperationType.COPY, 5, "to Documents", None)
    tfm.progress_manager.update_progress("document.pdf", 3)
    
    # Quick choice bar not active
    tfm.quick_choice_bar.mode = False
    tfm.draw_status()
    
    assert not tfm.quick_choice_bar.draw_called, "Quick choice bar should not be drawn"
    assert len(tfm.status_draws) > 0, "Progress text should be drawn"
    
    # Check progress content
    progress_text = " ".join([draw.split(": ", 1)[1] for draw in tfm.status_draws if ": " in draw])
    assert "Copying" in progress_text, f"Should contain 'Copying', got: {progress_text}"
    assert "3/5" in progress_text, f"Should contain '3/5', got: {progress_text}"
    
    tfm.progress_manager.finish_operation()
    
    print("✅ Progress without interference test passed!")


if __name__ == "__main__":
    test_progress_takes_priority()
    test_progress_without_quick_choice()
    print("\n🎉 All progress priority tests passed!")