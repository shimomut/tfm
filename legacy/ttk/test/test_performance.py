#!/usr/bin/env python3
"""
Unit tests for TTK performance monitoring.

Tests the PerformanceMonitor class to ensure accurate tracking of FPS,
rendering time, and other performance metrics.
"""

import time
import unittest
from ttk.demo.performance import PerformanceMonitor


class TestPerformanceMonitor(unittest.TestCase):
    """Test cases for PerformanceMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor(history_size=10)
    
    def test_initialization(self):
        """Test that monitor initializes correctly."""
        self.assertEqual(self.monitor.history_size, 10)
        self.assertEqual(self.monitor.get_total_frames(), 0)
        self.assertEqual(self.monitor.get_fps(), 0.0)
        self.assertEqual(self.monitor.get_render_time_ms(), 0.0)
    
    def test_frame_counting(self):
        """Test that frames are counted correctly."""
        # Simulate 5 frames
        for i in range(5):
            self.monitor.start_frame()
            time.sleep(0.01)  # Small delay between frames
        
        self.assertEqual(self.monitor.get_total_frames(), 5)
    
    def test_render_time_tracking(self):
        """Test that render time is tracked correctly."""
        # Simulate rendering
        self.monitor.start_render()
        time.sleep(0.01)  # Simulate 10ms render time
        self.monitor.end_render()
        
        render_time = self.monitor.get_render_time_ms()
        
        # Should be approximately 10ms (allow some variance)
        self.assertGreater(render_time, 5.0)
        self.assertLess(render_time, 20.0)
    
    def test_multiple_render_times(self):
        """Test tracking multiple render operations."""
        # Simulate multiple renders with different times
        for delay in [0.005, 0.010, 0.015]:
            self.monitor.start_render()
            time.sleep(delay)
            self.monitor.end_render()
        
        # Average should be around 10ms
        avg_time = self.monitor.get_render_time_ms()
        self.assertGreater(avg_time, 5.0)
        self.assertLess(avg_time, 20.0)
        
        # Min should be less than average
        min_time = self.monitor.get_min_render_time_ms()
        self.assertLess(min_time, avg_time)
        
        # Max should be greater than average
        max_time = self.monitor.get_max_render_time_ms()
        self.assertGreater(max_time, avg_time)
    
    def test_fps_calculation(self):
        """Test FPS calculation."""
        # Simulate frames at approximately 50 FPS (20ms per frame)
        for i in range(10):
            self.monitor.start_frame()
            time.sleep(0.02)
        
        fps = self.monitor.get_fps()
        
        # Should be approximately 50 FPS (allow variance)
        self.assertGreater(fps, 30.0)
        self.assertLess(fps, 70.0)
    
    def test_average_fps(self):
        """Test average FPS calculation over entire monitoring period."""
        # Simulate some frames
        for i in range(5):
            self.monitor.start_frame()
            time.sleep(0.01)
        
        avg_fps = self.monitor.get_average_fps()
        
        # Should have some reasonable FPS value
        self.assertGreater(avg_fps, 0.0)
        self.assertLess(avg_fps, 200.0)
    
    def test_frame_time_calculation(self):
        """Test frame time calculation."""
        # Simulate frames with known timing
        for i in range(5):
            self.monitor.start_frame()
            time.sleep(0.02)  # 20ms per frame
        
        frame_time = self.monitor.get_frame_time_ms()
        
        # Should be approximately 20ms
        self.assertGreater(frame_time, 15.0)
        self.assertLess(frame_time, 30.0)
    
    def test_uptime_tracking(self):
        """Test uptime tracking."""
        # Wait a bit
        time.sleep(0.1)
        
        uptime = self.monitor.get_uptime()
        
        # Should be at least 0.1 seconds
        self.assertGreaterEqual(uptime, 0.1)
    
    def test_history_size_limit(self):
        """Test that history is limited to specified size."""
        monitor = PerformanceMonitor(history_size=3)
        
        # Add more frames than history size
        for i in range(10):
            monitor.start_frame()
            time.sleep(0.01)
        
        # Should only keep last 3 frame times
        self.assertLessEqual(len(monitor.frame_times), 3)
    
    def test_reset(self):
        """Test that reset clears all statistics."""
        # Generate some data
        for i in range(5):
            self.monitor.start_frame()
            self.monitor.start_render()
            time.sleep(0.01)
            self.monitor.end_render()
        
        # Reset
        self.monitor.reset()
        
        # All metrics should be reset
        self.assertEqual(self.monitor.get_total_frames(), 0)
        self.assertEqual(self.monitor.get_fps(), 0.0)
        self.assertEqual(self.monitor.get_render_time_ms(), 0.0)
        self.assertEqual(len(self.monitor.frame_times), 0)
        self.assertEqual(len(self.monitor.render_times), 0)
    
    def test_get_summary(self):
        """Test that summary contains all expected metrics."""
        # Generate some data
        for i in range(3):
            self.monitor.start_frame()
            self.monitor.start_render()
            time.sleep(0.01)
            self.monitor.end_render()
        
        summary = self.monitor.get_summary()
        
        # Check all expected keys are present
        expected_keys = [
            'fps', 'average_fps', 'render_time_ms',
            'min_render_time_ms', 'max_render_time_ms',
            'frame_time_ms', 'total_frames', 'uptime'
        ]
        
        for key in expected_keys:
            self.assertIn(key, summary)
            self.assertIsInstance(summary[key], (int, float))
    
    def test_no_render_data(self):
        """Test behavior when no render data is available."""
        # Don't call start_render/end_render
        self.assertEqual(self.monitor.get_render_time_ms(), 0.0)
        self.assertEqual(self.monitor.get_min_render_time_ms(), 0.0)
        self.assertEqual(self.monitor.get_max_render_time_ms(), 0.0)
    
    def test_no_frame_data(self):
        """Test behavior when no frame data is available."""
        # Don't call start_frame
        self.assertEqual(self.monitor.get_fps(), 0.0)
        self.assertEqual(self.monitor.get_frame_time_ms(), 0.0)
    
    def test_render_without_end(self):
        """Test that incomplete render doesn't affect metrics."""
        # Start render but don't end it
        self.monitor.start_render()
        
        # Should still return 0 for render time
        self.assertEqual(self.monitor.get_render_time_ms(), 0.0)
    
    def test_concurrent_frames_and_renders(self):
        """Test tracking frames and renders together."""
        # Simulate realistic usage
        for i in range(5):
            self.monitor.start_frame()
            self.monitor.start_render()
            time.sleep(0.01)
            self.monitor.end_render()
            time.sleep(0.01)  # Additional frame time
        
        # Both metrics should be tracked
        self.assertGreater(self.monitor.get_fps(), 0.0)
        self.assertGreater(self.monitor.get_render_time_ms(), 0.0)
        self.assertEqual(self.monitor.get_total_frames(), 5)


class TestPerformanceMonitorEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def test_zero_history_size(self):
        """Test monitor with zero history size."""
        monitor = PerformanceMonitor(history_size=0)
        
        # Should handle gracefully
        monitor.start_frame()
        monitor.start_render()
        monitor.end_render()
        
        # Metrics should still work (using empty deque)
        self.assertEqual(monitor.get_fps(), 0.0)
        self.assertEqual(monitor.get_render_time_ms(), 0.0)
    
    def test_very_fast_frames(self):
        """Test with very fast frame rates."""
        monitor = PerformanceMonitor()
        
        # Simulate very fast frames (no delay)
        for i in range(10):
            monitor.start_frame()
        
        fps = monitor.get_fps()
        
        # Should handle very high FPS
        self.assertGreater(fps, 0.0)
    
    def test_multiple_resets(self):
        """Test multiple reset operations."""
        monitor = PerformanceMonitor()
        
        # Generate data, reset, repeat
        for cycle in range(3):
            for i in range(5):
                monitor.start_frame()
                time.sleep(0.01)
            
            monitor.reset()
            
            # Should be reset each time
            self.assertEqual(monitor.get_total_frames(), 0)


if __name__ == '__main__':
    unittest.main()
