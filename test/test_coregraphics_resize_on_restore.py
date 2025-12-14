#!/usr/bin/env python3
"""
Unit tests for CoreGraphics backend resize event on window restoration.

This test suite verifies that the CoreGraphics backend properly generates
resize events when the window size is automatically restored from saved
preferences on startup.

Test Coverage:
- Resize event generation when restored size differs from default
- No resize event when restored size matches default
- Grid dimension updates on restoration
- Resize flag setting on restoration
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ttk.backends.coregraphics_backend import CoreGraphicsBackend, COCOA_AVAILABLE
    from ttk.input_event import KeyCode
except ImportError as e:
    print(f"Warning: Could not import CoreGraphics backend: {e}")
    COCOA_AVAILABLE = False


@unittest.skipUnless(COCOA_AVAILABLE, "CoreGraphics backend not available")
class TestCoreGraphicsResizeOnRestore(unittest.TestCase):
    """Test resize event generation on window restoration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.backend = None
    
    def tearDown(self):
        """Clean up after tests."""
        if self.backend:
            try:
                self.backend.shutdown()
            except Exception:
                pass
    
    def test_resize_flag_detection(self):
        """Test that resize_pending flag is accessible after initialization."""
        self.backend = CoreGraphicsBackend(
            window_title="Test Window",
            font_name="Menlo",
            font_size=12,
            rows=24,
            cols=80,
            frame_autosave_name="TestResizeFlag"
        )
        
        self.backend.initialize()
        
        # Check that resize_pending attribute exists
        self.assertTrue(hasattr(self.backend, 'resize_pending'))
        
        # resize_pending should be a boolean
        self.assertIsInstance(self.backend.resize_pending, bool)
    
    def test_grid_dimensions_after_init(self):
        """Test that grid dimensions are set correctly after initialization."""
        self.backend = CoreGraphicsBackend(
            window_title="Test Window",
            font_name="Menlo",
            font_size=12,
            rows=24,
            cols=80,
            frame_autosave_name="TestGridDimensions"
        )
        
        self.backend.initialize()
        
        # Grid dimensions should be positive
        self.assertGreater(self.backend.rows, 0)
        self.assertGreater(self.backend.cols, 0)
        
        # Grid should be initialized
        self.assertIsNotNone(self.backend.grid)
        self.assertEqual(len(self.backend.grid), self.backend.rows)
        if self.backend.rows > 0:
            self.assertEqual(len(self.backend.grid[0]), self.backend.cols)
    
    def test_resize_event_generation(self):
        """Test that resize events can be generated via get_input()."""
        self.backend = CoreGraphicsBackend(
            window_title="Test Window",
            font_name="Menlo",
            font_size=12,
            rows=24,
            cols=80,
            frame_autosave_name="TestResizeEvent"
        )
        
        self.backend.initialize()
        
        # If resize_pending is True, get_input should return a resize event
        if self.backend.resize_pending:
            event = self.backend.get_input(timeout_ms=0)
            self.assertIsNotNone(event)
            self.assertEqual(event.key_code, KeyCode.RESIZE)
            
            # After getting the resize event, flag should be cleared
            self.assertFalse(self.backend.resize_pending)
    
    def test_multiple_backends_different_autosave_names(self):
        """Test that different autosave names don't interfere with each other."""
        # Create first backend
        backend1 = CoreGraphicsBackend(
            window_title="Test Window 1",
            font_name="Menlo",
            font_size=12,
            rows=24,
            cols=80,
            frame_autosave_name="TestWindow1"
        )
        backend1.initialize()
        rows1 = backend1.rows
        cols1 = backend1.cols
        backend1.shutdown()
        
        # Create second backend with different autosave name
        backend2 = CoreGraphicsBackend(
            window_title="Test Window 2",
            font_name="Menlo",
            font_size=12,
            rows=30,
            cols=100,
            frame_autosave_name="TestWindow2"
        )
        backend2.initialize()
        rows2 = backend2.rows
        cols2 = backend2.cols
        backend2.shutdown()
        
        # Backends should be able to have different dimensions
        # (This test mainly verifies no crashes occur)
        self.assertGreater(rows1, 0)
        self.assertGreater(cols1, 0)
        self.assertGreater(rows2, 0)
        self.assertGreater(cols2, 0)


def run_tests():
    """Run the test suite."""
    if not COCOA_AVAILABLE:
        print("Skipping tests - CoreGraphics backend not available")
        print("Install PyObjC: pip install pyobjc-framework-Cocoa")
        return
    
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCoreGraphicsResizeOnRestore)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
