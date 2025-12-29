"""
Test that log updates trigger redraws

Run with: PYTHONPATH=.:src:ttk pytest test/test_log_redraw_trigger.py -v
"""

import unittest
import tempfile
import time
from unittest.mock import Mock, patch

from tfm_log_manager import LogManager, LogCapture

class TestLogRedrawTrigger(unittest.TestCase):
    """Test log update detection and redraw triggering"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock config
        self.mock_config = Mock()
        self.mock_config.MAX_LOG_MESSAGES = 100
    
    def test_log_manager_tracks_updates(self):
        """Test that LogManager tracks when new messages are added"""
        log_manager = LogManager(self.mock_config)
        
        # Initially no updates
        self.assertFalse(log_manager.has_log_updates())
        
        # Add a message directly
        log_manager.add_message("TEST", "Test message")
        
        # Should detect update
        self.assertTrue(log_manager.has_log_updates())
        
        # Mark as processed
        log_manager.mark_log_updates_processed()
        
        # Should no longer detect update
        self.assertFalse(log_manager.has_log_updates())
    
    def test_log_capture_triggers_updates(self):
        """Test that LogCapture triggers update notifications"""
        log_manager = LogManager(self.mock_config)
        
        # Initially no updates
        self.assertFalse(log_manager.has_log_updates())
        
        # Simulate stdout write (which goes through LogCapture)
        print("Test stdout message")
        
        # Should detect update
        self.assertTrue(log_manager.has_log_updates())
        
        # Mark as processed
        log_manager.mark_log_updates_processed()
        
        # Should no longer detect update
        self.assertFalse(log_manager.has_log_updates())
    
    def test_stderr_capture_triggers_updates(self):
        """Test that stderr capture also triggers update notifications"""
        log_manager = LogManager(self.mock_config)
        
        # Initially no updates
        self.assertFalse(log_manager.has_log_updates())
        
        # Simulate stderr write
        print("Test stderr message", file=sys.stderr)
        
        # Should detect update
        self.assertTrue(log_manager.has_log_updates())
        
        # Mark as processed
        log_manager.mark_log_updates_processed()
        
        # Should no longer detect update
        self.assertFalse(log_manager.has_log_updates())
    
    def test_startup_messages_trigger_updates(self):
        """Test that startup messages trigger update notifications"""
        log_manager = LogManager(self.mock_config)
        
        # Initially no updates (startup messages are added during init)
        # But let's clear the flag first
        log_manager.mark_log_updates_processed()
        self.assertFalse(log_manager.has_log_updates())
        
        # Add startup messages
        log_manager.add_startup_messages("1.0", "https://github.com/test", "Test App")
        
        # Should detect update
        self.assertTrue(log_manager.has_log_updates())
    
    def test_multiple_messages_tracked_correctly(self):
        """Test that multiple messages are tracked correctly"""
        log_manager = LogManager(self.mock_config)
        
        # Clear initial state
        log_manager.mark_log_updates_processed()
        self.assertFalse(log_manager.has_log_updates())
        
        # Add multiple messages
        log_manager.add_message("TEST1", "Message 1")
        self.assertTrue(log_manager.has_log_updates())
        
        log_manager.add_message("TEST2", "Message 2")
        self.assertTrue(log_manager.has_log_updates())
        
        # Mark as processed
        log_manager.mark_log_updates_processed()
        self.assertFalse(log_manager.has_log_updates())
        
        # Add another message
        log_manager.add_message("TEST3", "Message 3")
        self.assertTrue(log_manager.has_log_updates())
    
    def test_log_capture_callback_mechanism(self):
        """Test the callback mechanism in LogCapture"""
        from collections import deque
        
        # Create a mock callback
        update_callback = Mock()
        
        # Create LogCapture with callback
        log_messages = deque(maxlen=100)
        log_capture = LogCapture(log_messages, "TEST", None, update_callback)
        
        # Write a message
        log_capture.write("Test message")
        
        # Callback should have been called
        update_callback.assert_called_once()
        
        # Write another message
        log_capture.write("Another message")
        
        # Callback should have been called again
        self.assertEqual(update_callback.call_count, 2)
    
    def test_empty_messages_dont_trigger_updates(self):
        """Test that empty messages don't trigger updates"""
        from collections import deque
        
        update_callback = Mock()
        log_messages = deque(maxlen=100)
        log_capture = LogCapture(log_messages, "TEST", None, update_callback)
        
        # Write empty/whitespace messages
        log_capture.write("")
        log_capture.write("   ")
        log_capture.write("\n")
        log_capture.write("\t")
        
        # Callback should not have been called
        update_callback.assert_not_called()
        
        # Write a real message
        log_capture.write("Real message")
        
        # Now callback should be called
        update_callback.assert_called_once()
    
    def test_message_count_tracking(self):
        """Test that message count is tracked correctly"""
        log_manager = LogManager(self.mock_config)
        
        # Get initial count
        initial_count = len(log_manager.log_messages)
        log_manager.mark_log_updates_processed()
        
        # Add a message
        log_manager.add_message("TEST", "Message")
        
        # Count should have changed
        self.assertEqual(len(log_manager.log_messages), initial_count + 1)
        self.assertTrue(log_manager.has_log_updates())
        
        # Mark as processed
        log_manager.mark_log_updates_processed()
        self.assertFalse(log_manager.has_log_updates())
        
        # Count should be updated
        self.assertEqual(log_manager.last_message_count, len(log_manager.log_messages))
    
    def tearDown(self):
        """Clean up after tests"""
        # Restore original stdout/stderr if they were modified
        # This is handled by LogManager.__del__ but let's be explicit
        pass
