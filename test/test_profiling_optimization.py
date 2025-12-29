"""
Test: Profiling Optimization

Tests the profiling overhead optimizations to ensure they work correctly.

Run with: PYTHONPATH=.:src:ttk pytest test/test_profiling_optimization.py -v
"""

import time
import unittest

from tfm_profiling import ProfilingManager


class TestProfilingOptimization(unittest.TestCase):
    """Test profiling optimization features"""
    
    def test_disabled_profiling_has_zero_overhead(self):
        """Test that disabled profiling has minimal overhead"""
        # Create disabled profiling manager
        profiler = ProfilingManager(enabled=False)
        
        # These should all return immediately
        profiler.start_frame()
        profiler.end_frame()
        self.assertFalse(profiler.should_print_fps())
        profiler.print_fps()
        
        # Profile methods should just call the function
        def test_func():
            return 42
        
        result = profiler.profile_key_handling(test_func)
        self.assertEqual(result, 42)
        
        result = profiler.profile_rendering(test_func)
        self.assertEqual(result, 42)
    
    def test_conditional_rendering_profiling(self):
        """Test that rendering is profiled conditionally"""
        # Create profiling manager with interval of 10
        profiler = ProfilingManager(enabled=True, render_profile_interval=10)
        
        def test_func():
            return "rendered"
        
        # Call profile_rendering 25 times
        for i in range(25):
            result = profiler.profile_rendering(test_func)
            self.assertEqual(result, "rendered")
        
        # Wait for background threads
        time.sleep(0.5)
        
        # Should have profiled at calls 10 and 20
        self.assertEqual(profiler.render_profile_count, 2)
    
    def test_key_handling_always_profiled(self):
        """Test that key handling is always profiled"""
        profiler = ProfilingManager(enabled=True)
        
        def test_func():
            return "key"
        
        # Call profile_key_handling 5 times
        for i in range(5):
            result = profiler.profile_key_handling(test_func)
            self.assertEqual(result, "key")
        
        # Wait for background threads
        time.sleep(0.5)
        
        # Should have profiled all 5 calls
        self.assertEqual(profiler.key_profile_count, 5)
    
    def test_fps_tracker_uses_deque(self):
        """Test that FPS tracker uses deque with maxlen"""
        profiler = ProfilingManager(enabled=True)
        
        # Record more frames than the window size
        for i in range(100):
            profiler.start_frame()
            time.sleep(0.001)
        
        # Should only keep the most recent frames
        self.assertEqual(len(profiler.fps_tracker.frame_times), 
                        profiler.fps_tracker.frame_times.maxlen)
    
    def test_async_file_io_does_not_block(self):
        """Test that file I/O happens asynchronously"""
        profiler = ProfilingManager(enabled=True)
        
        def test_func():
            # Simulate some work
            total = 0
            for i in range(100):
                total += i
            return total
        
        # Measure time for profiling
        start_time = time.time()
        
        # Profile 5 operations
        for i in range(5):
            profiler.profile_key_handling(test_func)
        
        elapsed_time = time.time() - start_time
        
        # Should complete quickly (< 0.1s) because file I/O is async
        self.assertLess(elapsed_time, 0.1)
        
        # Wait for background threads to complete
        time.sleep(0.5)
        
        # All profiles should be written
        self.assertEqual(profiler.key_profile_count, 5)
    
    def test_early_return_optimization(self):
        """Test that disabled profiling returns early"""
        profiler = ProfilingManager(enabled=False)
        
        # These should all be None or False
        self.assertIsNone(profiler.fps_tracker)
        self.assertIsNone(profiler.profile_writer)
        
        # Methods should return immediately without error
        profiler.start_frame()
        profiler.end_frame()
        self.assertFalse(profiler.should_print_fps())
        profiler.print_fps()
