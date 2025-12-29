"""
Test TFM with CoreGraphics Backend Integration

This test verifies that TFM can initialize and run with the CoreGraphicsBackend
on macOS, checking basic functionality, rendering, and input handling.

Requirements tested:
- 6.4: Backend initialization and selection
- 6.5: Feature equivalence between backends
- 11.5: Error handling and graceful degradation

Run with: PYTHONPATH=.:src:ttk pytest test/test_coregraphics_backend_integration.py -v
"""

from pathlib import Path
import platform
import unittest


class TestCoreGraphicsBackendIntegration(unittest.TestCase):
    """Test TFM integration with CoreGraphics backend"""
    
    def setUp(self):
        """Set up test environment"""
        self.is_macos = platform.system() == 'Darwin'
        self.has_pyobjc = False
        
        try:
            import objc
            self.has_pyobjc = True
        except ImportError:
            pass
    
    def test_platform_detection(self):
        """Test that platform detection works correctly"""
        # This test should pass on any platform
        detected_platform = platform.system()
        self.assertIn(detected_platform, ['Darwin', 'Linux', 'Windows'])
        
        if self.is_macos:
            print("✓ Running on macOS - CoreGraphics backend available")
        else:
            print(f"✓ Running on {detected_platform} - CoreGraphics backend not available")
    
    def test_pyobjc_availability(self):
        """Test PyObjC availability check"""
        if self.is_macos:
            if self.has_pyobjc:
                print("✓ PyObjC is available - CoreGraphics backend can be used")
            else:
                print("⚠ PyObjC is not available - CoreGraphics backend will fall back to curses")
        else:
            print("✓ Not on macOS - PyObjC check skipped")
    
    @unittest.skipUnless(platform.system() == 'Darwin', "CoreGraphics backend only available on macOS")
    def test_coregraphics_backend_import(self):
        """Test that CoreGraphics backend can be imported on macOS"""
        try:
            import objc
        except ImportError:
            self.skipTest("PyObjC not available")
        
        try:
            from ttk.backends.coregraphics_backend import CoreGraphicsBackend
            print("✓ CoreGraphicsBackend imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import CoreGraphicsBackend: {e}")
    
    @unittest.skipUnless(platform.system() == 'Darwin', "CoreGraphics backend only available on macOS")
    def test_coregraphics_backend_instantiation(self):
        """Test that CoreGraphics backend can be instantiated"""
        try:
            import objc
        except ImportError:
            self.skipTest("PyObjC not available")
        
        from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        
        # Create backend with correct parameters
        try:
            renderer = CoreGraphicsBackend(
                window_title='TFM Test',
                font_names=['Menlo'],
                font_size=14,
                rows=24,
                cols=80
            )
            print("✓ CoreGraphicsBackend instantiated successfully")
            self.assertIsNotNone(renderer)
        except Exception as e:
            self.fail(f"Failed to instantiate CoreGraphicsBackend: {e}")
    
    def test_backend_selector_with_coregraphics(self):
        """Test backend selector with CoreGraphics request"""
        from tfm_backend_selector import select_backend
        
        # Create mock args object requesting CoreGraphics
        class MockArgs:
            backend = 'coregraphics'
            desktop = False
        
        args = MockArgs()
        backend_name, backend_options = select_backend(args)
        
        if self.is_macos and self.has_pyobjc:
            # Should select CoreGraphics on macOS with PyObjC
            self.assertEqual(backend_name, 'coregraphics')
            self.assertIn('window_title', backend_options)
            self.assertIn('font_name', backend_options)
            self.assertIn('font_size', backend_options)
            print("✓ Backend selector correctly selected CoreGraphics")
        else:
            # Should fall back to curses on non-macOS or without PyObjC
            self.assertEqual(backend_name, 'curses')
            print("✓ Backend selector correctly fell back to curses")
    
    def test_backend_selector_with_desktop_flag(self):
        """Test backend selector with --desktop flag"""
        from tfm_backend_selector import select_backend
        
        # Create mock args object with desktop flag
        class MockArgs:
            backend = None
            desktop = True
        
        args = MockArgs()
        backend_name, backend_options = select_backend(args)
        
        if self.is_macos and self.has_pyobjc:
            # Should select CoreGraphics on macOS with PyObjC
            self.assertEqual(backend_name, 'coregraphics')
            print("✓ --desktop flag correctly selected CoreGraphics")
        else:
            # Should fall back to curses on non-macOS or without PyObjC
            self.assertEqual(backend_name, 'curses')
            print("✓ --desktop flag correctly fell back to curses")
    
    def test_backend_fallback_on_non_macos(self):
        """Test that CoreGraphics request falls back to curses on non-macOS"""
        from tfm_backend_selector import select_backend
        
        # Create mock args requesting CoreGraphics
        class MockArgs:
            backend = 'coregraphics'
            desktop = False
        
        args = MockArgs()
        backend_name, backend_options = select_backend(args)
        
        if not self.is_macos:
            # Should always fall back to curses on non-macOS
            self.assertEqual(backend_name, 'curses')
            self.assertEqual(backend_options, {})
            print("✓ CoreGraphics request correctly fell back to curses on non-macOS")
        else:
            print("✓ Running on macOS - fallback test skipped")
    
    @unittest.skipUnless(platform.system() == 'Darwin', "CoreGraphics backend only available on macOS")
    def test_coregraphics_renderer_api_compliance(self):
        """Test that CoreGraphics backend implements required Renderer API"""
        try:
            import objc
        except ImportError:
            self.skipTest("PyObjC not available")
        
        from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        from ttk.renderer import Renderer
        
        # Verify CoreGraphicsBackend is a subclass of Renderer
        self.assertTrue(issubclass(CoreGraphicsBackend, Renderer))
        print("✓ CoreGraphicsBackend is a proper Renderer subclass")
        
        # Check that required methods exist
        required_methods = [
            'initialize',
            'shutdown',
            'clear',
            'refresh',
            'get_dimensions',
            'draw_text',
            'draw_hline',
            'draw_vline',
            'draw_rect',
            'get_input',
            'init_color_pair',
            'set_cursor_visibility',
        ]
        
        for method_name in required_methods:
            self.assertTrue(hasattr(CoreGraphicsBackend, method_name),
                          f"CoreGraphicsBackend missing required method: {method_name}")
        
        print(f"✓ CoreGraphicsBackend implements all {len(required_methods)} required methods")
    
    def test_tfm_main_accepts_renderer(self):
        """Test that tfm_main can accept a renderer instance"""
        from tfm_main import main as tfm_main
        import inspect
        
        # Check tfm_main signature
        sig = inspect.signature(tfm_main)
        params = list(sig.parameters.keys())
        
        # First parameter should be 'renderer'
        self.assertGreater(len(params), 0, "tfm_main has no parameters")
        self.assertEqual(params[0], 'renderer', 
                        f"First parameter should be 'renderer', got '{params[0]}'")
        
        print("✓ tfm_main correctly accepts renderer as first parameter")
    
    def test_color_system_rgb_support(self):
        """Test that color system supports RGB colors for CoreGraphics"""
        from tfm_colors import COLOR_SCHEMES
        
        # Get a color scheme
        colors = COLOR_SCHEMES.get('dark', {})
        
        # Verify colors are RGB tuples
        for color_name, color_def in colors.items():
            # Each color definition should have 'rgb' key
            self.assertIn('rgb', color_def, f"Color {color_name} missing 'rgb' key")
            
            rgb = color_def['rgb']
            
            # Check RGB is a tuple
            self.assertIsInstance(rgb, tuple, f"RGB for {color_name} is not a tuple")
            self.assertEqual(len(rgb), 3, f"RGB for {color_name} should have 3 components")
            
            # Check RGB values are in valid range
            for component in rgb:
                self.assertIsInstance(component, int, "RGB component should be an integer")
                self.assertGreaterEqual(component, 0, "RGB component should be >= 0")
                self.assertLessEqual(component, 255, "RGB component should be <= 255")
        
        print(f"✓ Color system uses RGB tuples ({len(colors)} colors verified)")


class TestCoreGraphicsBackendErrorHandling(unittest.TestCase):
    """Test error handling for CoreGraphics backend"""
    
    def test_graceful_fallback_message(self):
        """Test that fallback to curses provides helpful error messages"""
        import io
        from contextlib import redirect_stderr
        from tfm_backend_selector import select_backend
        
        # Create mock args requesting CoreGraphics
        class MockArgs:
            backend = 'coregraphics'
            desktop = False
        
        args = MockArgs()
        
        # Capture stderr
        stderr_capture = io.StringIO()
        
        with redirect_stderr(stderr_capture):
            backend_name, backend_options = select_backend(args)
        
        stderr_output = stderr_capture.getvalue()
        
        # On non-macOS, should see error message
        if platform.system() != 'Darwin':
            self.assertIn('CoreGraphics backend is only available on macOS', stderr_output)
            self.assertIn('Falling back to curses backend', stderr_output)
            print("✓ Helpful error message provided for non-macOS platform")
        else:
            print("✓ Running on macOS - error message test skipped")
    
    def test_pyobjc_missing_message(self):
        """Test error message when PyObjC is missing on macOS"""
        # This test is informational - we can't easily simulate missing PyObjC
        if platform.system() == 'Darwin':
            try:
                import objc
                print("✓ PyObjC is installed - missing PyObjC test skipped")
            except ImportError:
                print("⚠ PyObjC is not installed - would see fallback message")


def run_manual_coregraphics_test():
    """
    Manual test instructions for running TFM with CoreGraphics backend.
    
    This function prints instructions for manually testing TFM with the
    CoreGraphics backend, which requires a GUI environment.
    """
    print("\n" + "="*70)
    print("MANUAL COREGRAPHICS BACKEND TEST INSTRUCTIONS")
    print("="*70)
    print()
    print("To manually test TFM with the CoreGraphics backend:")
    print()
    print("1. Run TFM with CoreGraphics backend:")
    print("   python3 tfm.py --backend coregraphics")
    print()
    print("   Or use the shorthand:")
    print("   python3 tfm.py --desktop")
    print()
    print("2. Verify the following:")
    print("   ✓ A native macOS window opens")
    print("   ✓ TFM interface is rendered correctly")
    print("   ✓ File lists are visible in both panes")
    print("   ✓ Colors are displayed correctly")
    print("   ✓ Status bar shows current directory")
    print()
    print("3. Test basic functionality:")
    print("   ✓ Arrow keys navigate file list")
    print("   ✓ Tab switches between panes")
    print("   ✓ Enter opens directories")
    print("   ✓ Backspace goes to parent directory")
    print("   ✓ Space selects/deselects files")
    print("   ✓ Q quits the application")
    print()
    print("4. Test rendering:")
    print("   ✓ Text is crisp and readable")
    print("   ✓ No rendering artifacts or glitches")
    print("   ✓ Window can be resized")
    print("   ✓ Interface adapts to window size")
    print()
    print("5. Test input handling:")
    print("   ✓ All key bindings work as expected")
    print("   ✓ Special keys (F1-F12) work")
    print("   ✓ Modifier keys (Cmd, Ctrl, Alt) work")
    print("   ✓ Mouse input works (if supported)")
    print()
    print("="*70)
    print()
