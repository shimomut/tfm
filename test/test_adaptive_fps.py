"""
Tests for Adaptive FPS Manager

Run with: PYTHONPATH=.:src:ttk pytest test/test_adaptive_fps.py -v
"""

import unittest
import time

from src.tfm_adaptive_fps import AdaptiveFPSManager


class TestAdaptiveFPSManager(unittest.TestCase):
    """Test cases for AdaptiveFPSManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.fps_manager = AdaptiveFPSManager()
    
    def test_initial_state(self):
        """Test initial FPS is 60"""
        self.assertEqual(self.fps_manager.get_current_fps(), 60)
        self.assertEqual(self.fps_manager.get_timeout_ms(), 16)
    
    def test_mark_activity_resets_fps(self):
        """Test that marking activity resets to 60 FPS"""
        # Simulate idle time
        time.sleep(0.6)
        
        # Should be at lower FPS
        timeout = self.fps_manager.get_timeout_ms()
        self.assertGreater(timeout, 16)
        
        # Mark activity
        self.fps_manager.mark_activity()
        
        # Should be back to 60 FPS
        self.assertEqual(self.fps_manager.get_current_fps(), 60)
        self.assertEqual(self.fps_manager.get_timeout_ms(), 16)
    
    def test_fps_degradation_levels(self):
        """Test FPS degrades through expected levels"""
        # Start at 60 FPS
        self.assertEqual(self.fps_manager.get_current_fps(), 60)
        
        # After 0.5s, should be at 30 FPS
        time.sleep(0.6)
        self.fps_manager.get_timeout_ms()
        self.assertEqual(self.fps_manager.get_current_fps(), 30)
        
        # After 2s total, should be at 15 FPS
        time.sleep(1.5)
        self.fps_manager.get_timeout_ms()
        self.assertEqual(self.fps_manager.get_current_fps(), 15)
    
    def test_is_idle(self):
        """Test idle state detection"""
        # Initially not idle
        self.assertFalse(self.fps_manager.is_idle())
        
        # After degradation, should be idle
        time.sleep(0.6)
        self.fps_manager.get_timeout_ms()
        self.assertTrue(self.fps_manager.is_idle())
        
        # After activity, not idle again
        self.fps_manager.mark_activity()
        self.assertFalse(self.fps_manager.is_idle())
    
    def test_timeout_values_match_fps_levels(self):
        """Test that timeout values correspond to correct FPS levels"""
        expected_timeouts = {
            60: 16,
            30: 33,
            15: 66,
            5: 200,
            1: 1000,
        }
        
        for fps, expected_timeout in expected_timeouts.items():
            # Find this FPS level in the manager
            for i, (level_fps, level_timeout) in enumerate(AdaptiveFPSManager.FPS_LEVELS):
                if level_fps == fps:
                    self.assertEqual(level_timeout, expected_timeout,
                                   f"FPS {fps} should have timeout {expected_timeout}ms")
                    break
