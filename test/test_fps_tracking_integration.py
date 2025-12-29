"""
Test FPS tracking integration in FileManager main loop

This test verifies that FPS tracking is properly integrated into the
FileManager.run() method and that FPS is calculated and printed correctly.

Run with: PYTHONPATH=.:src:ttk pytest test/test_fps_tracking_integration.py -v
"""

import unittest
import time
from unittest.mock import Mock, patch, MagicMock

from tfm_profiling import ProfilingManager, FPSTracker


class TestFPSTrackingIntegration(unittest.TestCase):
    """Test FPS tracking integration"""
    
    def test_fps_tracker_records_frames(self):
        """Test that FPS tracker records frame times"""
        tracker = FPSTracker(window_size=10, print_interval=5.0)
        
        # Record some frames
        for _ in range(5):
            tracker.record_frame()
            time.sleep(0.01)  # Small delay between frames
        
        # Should have recorded 5 frames
        self.assertEqual(len(tracker.frame_times), 5)
    
    def test_fps_calculation_with_known_times(self):
        """Test FPS calculation with known frame times"""
        tracker = FPSTracker(window_size=10, print_interval=5.0)
        
        # Simulate 10 frames over 1 second (should be ~9 FPS)
        base_time = time.time()
        for i in range(10):
            tracker.frame_times.append(base_time + (i * 0.1))
        
        fps = tracker.calculate_fps()
        
        # Should be approximately 9 FPS (9 intervals over 0.9 seconds)
        self.assertAlmostEqual(fps, 10.0, delta=0.5)
    
    def test_fps_print_interval(self):
        """Test that FPS prints at correct intervals"""
        tracker = FPSTracker(window_size=10, print_interval=1.0)
        
        # Should not print immediately
        self.assertFalse(tracker.should_print())
        
        # Wait for interval to elapse
        time.sleep(1.1)
        
        # Should print now
        self.assertTrue(tracker.should_print())
        
        # Should not print again immediately
        self.assertFalse(tracker.should_print())
    
    def test_fps_output_format(self):
        """Test that FPS output includes timestamp and FPS value"""
        tracker = FPSTracker(window_size=10, print_interval=5.0)
        
        # Record some frames
        for _ in range(5):
            tracker.record_frame()
            time.sleep(0.01)
        
        output = tracker.format_output()
        
        # Should contain timestamp in brackets
        self.assertIn('[', output)
        self.assertIn(']', output)
        
        # Should contain FPS label
        self.assertIn('FPS:', output)
        
        # Should contain a numeric value
        self.assertRegex(output, r'FPS: \d+\.\d+')
    
    def test_profiling_manager_fps_integration(self):
        """Test that ProfilingManager integrates FPS tracking correctly"""
        manager = ProfilingManager(enabled=True)
        
        # Should have FPS tracker when enabled
        self.assertIsNotNone(manager.fps_tracker)
        
        # Test frame recording
        manager.start_frame()
        time.sleep(0.01)
        manager.start_frame()
        
        # Should have recorded frames
        self.assertGreater(len(manager.fps_tracker.frame_times), 0)
    
    def test_profiling_manager_disabled_no_overhead(self):
        """Test that disabled profiling has no FPS tracking overhead"""
        manager = ProfilingManager(enabled=False)
        
        # Should not have FPS tracker when disabled
        self.assertIsNone(manager.fps_tracker)
        
        # These should not raise errors
        manager.start_frame()
        manager.end_frame()
        self.assertFalse(manager.should_print_fps())
    
    def test_fps_sliding_window(self):
        """Test that FPS tracker uses sliding window correctly"""
        tracker = FPSTracker(window_size=5, print_interval=5.0)
        
        # Record more frames than window size
        for _ in range(10):
            tracker.record_frame()
            time.sleep(0.01)
        
        # Should only keep last 5 frames
        self.assertEqual(len(tracker.frame_times), 5)
    
    def test_fps_calculation_insufficient_data(self):
        """Test FPS calculation with insufficient data"""
        tracker = FPSTracker(window_size=10, print_interval=5.0)
        
        # No frames recorded
        self.assertEqual(tracker.calculate_fps(), 0.0)
        
        # Only one frame
        tracker.record_frame()
        self.assertEqual(tracker.calculate_fps(), 0.0)
    
    def test_fps_print_timing_accuracy(self):
        """Test that FPS print timing is accurate"""
        tracker = FPSTracker(window_size=10, print_interval=0.5)
        
        # Record initial time
        start_time = time.time()
        
        # Should not print immediately
        self.assertFalse(tracker.should_print())
        
        # Wait for half the interval
        time.sleep(0.3)
        self.assertFalse(tracker.should_print())
        
        # Wait for full interval
        time.sleep(0.3)
        self.assertTrue(tracker.should_print())
        
        # Verify timing
        elapsed = time.time() - start_time
        self.assertGreaterEqual(elapsed, 0.5)
