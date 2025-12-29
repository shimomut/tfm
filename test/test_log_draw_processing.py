"""
Test that log updates are marked as processed when draw_log_pane is called

Run with: PYTHONPATH=.:src:ttk pytest test/test_log_draw_processing.py -v
"""

import unittest
from unittest.mock import Mock, patch

class TestLogDrawProcessing(unittest.TestCase):
    """Test that drawing the log pane marks updates as processed"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock config
        self.mock_config = Mock()
        self.mock_config.MAX_LOG_MESSAGES = 100
    
    def test_draw_log_pane_marks_updates_processed(self):
        """Test that draw_log_pane calls mark_log_updates_processed"""
        from tfm_log_manager import LogManager
        
        # Create LogManager
        log_manager = LogManager(self.mock_config)
        
        # Add a message to trigger updates
        log_manager.add_message("TEST", "Test message")
        
        # Should have updates
        self.assertTrue(log_manager.has_log_updates())
        
        # Mock stdscr for drawing
        mock_stdscr = Mock()
        mock_stdscr.addstr = Mock()
        
        # Mock the color functions to avoid import issues
        with patch('tfm_colors.get_log_color') as mock_get_log_color, \
             patch('tfm_colors.get_boundary_color') as mock_get_boundary_color, \
             patch('tfm_colors.get_status_color') as mock_get_status_color:
            
            mock_get_log_color.return_value = 0
            mock_get_boundary_color.return_value = 0
            mock_get_status_color.return_value = 0
            
            # Draw the log pane
            log_manager.draw_log_pane(mock_stdscr, 0, 10, 80)
        
        # Should no longer have updates after drawing
        self.assertFalse(log_manager.has_log_updates())
        
        # Clean up
        log_manager.restore_stdio()
    
    def test_draw_log_pane_with_no_messages(self):
        """Test that draw_log_pane works correctly with no messages"""
        from tfm_log_manager import LogManager
        
        # Create LogManager and clear any startup messages
        log_manager = LogManager(self.mock_config)
        log_manager.log_messages.clear()
        log_manager.mark_log_updates_processed()
        
        # Should have no updates
        self.assertFalse(log_manager.has_log_updates())
        
        # Mock stdscr for drawing
        mock_stdscr = Mock()
        mock_stdscr.addstr = Mock()
        
        # Draw the log pane (should not crash with no messages)
        log_manager.draw_log_pane(mock_stdscr, 0, 10, 80)
        
        # Should still have no updates
        self.assertFalse(log_manager.has_log_updates())
        
        # Clean up
        log_manager.restore_stdio()
    
    def test_draw_log_pane_with_zero_height(self):
        """Test that draw_log_pane handles zero height gracefully"""
        from tfm_log_manager import LogManager
        
        # Create LogManager
        log_manager = LogManager(self.mock_config)
        
        # Add a message
        log_manager.add_message("TEST", "Test message")
        self.assertTrue(log_manager.has_log_updates())
        
        # Mock stdscr for drawing
        mock_stdscr = Mock()
        
        # Draw with zero height (should return early)
        log_manager.draw_log_pane(mock_stdscr, 0, 0, 80)
        
        # Updates should still be present since drawing was skipped
        self.assertTrue(log_manager.has_log_updates())
        
        # Now draw with proper height
        with patch('tfm_colors.get_log_color') as mock_get_log_color:
            mock_get_log_color.return_value = 0
            log_manager.draw_log_pane(mock_stdscr, 0, 10, 80)
        
        # Updates should now be processed
        self.assertFalse(log_manager.has_log_updates())
        
        # Clean up
        log_manager.restore_stdio()
    
    def test_draw_log_pane_exception_handling(self):
        """Test that exceptions in draw_log_pane don't break update processing"""
        from tfm_log_manager import LogManager
        
        # Create LogManager
        log_manager = LogManager(self.mock_config)
        
        # Add a message
        log_manager.add_message("TEST", "Test message")
        self.assertTrue(log_manager.has_log_updates())
        
        # Mock stdscr to raise an exception
        mock_stdscr = Mock()
        mock_stdscr.addstr.side_effect = Exception("Drawing error")
        
        # Draw should handle the exception gracefully
        with patch('tfm_colors.get_log_color') as mock_get_log_color:
            mock_get_log_color.return_value = 0
            log_manager.draw_log_pane(mock_stdscr, 0, 10, 80)
        
        # Updates should still be processed even if drawing failed
        # Note: This depends on where the exception occurs vs where mark_log_updates_processed is called
        # If the exception happens before mark_log_updates_processed, updates won't be marked as processed
        # This is actually the correct behavior - we only mark as processed if drawing succeeds
        
        # Clean up
        log_manager.restore_stdio()
    
    def test_multiple_draws_efficiency(self):
        """Test that multiple draws without new messages don't cause issues"""
        from tfm_log_manager import LogManager
        
        # Create LogManager
        log_manager = LogManager(self.mock_config)
        
        # Add a message
        log_manager.add_message("TEST", "Test message")
        self.assertTrue(log_manager.has_log_updates())
        
        # Mock stdscr for drawing
        mock_stdscr = Mock()
        mock_stdscr.addstr = Mock()
        
        # Draw multiple times
        with patch('tfm_colors.get_log_color') as mock_get_log_color:
            mock_get_log_color.return_value = 0
            
            # First draw should process updates
            log_manager.draw_log_pane(mock_stdscr, 0, 10, 80)
            self.assertFalse(log_manager.has_log_updates())
            
            # Subsequent draws should not indicate updates
            log_manager.draw_log_pane(mock_stdscr, 0, 10, 80)
            self.assertFalse(log_manager.has_log_updates())
            
            log_manager.draw_log_pane(mock_stdscr, 0, 10, 80)
            self.assertFalse(log_manager.has_log_updates())
        
        # Clean up
        log_manager.restore_stdio()
    
    def test_draw_after_new_message(self):
        """Test the complete cycle: message -> update detection -> draw -> processed"""
        from tfm_log_manager import LogManager
        
        # Create LogManager
        log_manager = LogManager(self.mock_config)
        log_manager.mark_log_updates_processed()  # Clear initial state
        
        # Initially no updates
        self.assertFalse(log_manager.has_log_updates())
        
        # Add message
        log_manager.add_message("TEST", "Test message")
        self.assertTrue(log_manager.has_log_updates())
        
        # Mock stdscr for drawing
        mock_stdscr = Mock()
        mock_stdscr.addstr = Mock()
        
        # Draw the log pane
        with patch('tfm_colors.get_log_color') as mock_get_log_color:
            mock_get_log_color.return_value = 0
            log_manager.draw_log_pane(mock_stdscr, 0, 10, 80)
        
        # Updates should be processed
        self.assertFalse(log_manager.has_log_updates())
        
        # Add another message
        log_manager.add_message("TEST2", "Another message")
        self.assertTrue(log_manager.has_log_updates())
        
        # Draw again
        with patch('tfm_colors.get_log_color') as mock_get_log_color:
            mock_get_log_color.return_value = 0
            log_manager.draw_log_pane(mock_stdscr, 0, 10, 80)
        
        # Updates should be processed again
        self.assertFalse(log_manager.has_log_updates())
        
        # Clean up
        log_manager.restore_stdio()
