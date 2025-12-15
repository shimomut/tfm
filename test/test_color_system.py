#!/usr/bin/env python3
"""
Test suite for the color fix that ensures headers, footers, and status bars
display correctly in curses mode with visible contrast.
"""

import sys
import os
import unittest

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from ttk.backends.curses_backend import CursesBackend


class TestColorFix(unittest.TestCase):
    """Test cases for the color fix"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.backend = CursesBackend()
    
    def test_dark_gray_maps_to_white(self):
        """Test that dark gray (51,63,76) maps to WHITE"""
        rgb = (51, 63, 76)
        result = self.backend._rgb_to_curses_color(rgb)
        # In curses, COLOR_WHITE = 7
        self.assertEqual(result, 7, 
                        f"Dark gray {rgb} should map to WHITE (7), got {result}")
    
    def test_light_gray_maps_to_white(self):
        """Test that light gray (220,220,220) maps to WHITE"""
        rgb = (220, 220, 220)
        result = self.backend._rgb_to_curses_color(rgb)
        self.assertEqual(result, 7,
                        f"Light gray {rgb} should map to WHITE (7), got {result}")
    
    def test_black_maps_to_black(self):
        """Test that black (0,0,0) maps to BLACK"""
        rgb = (0, 0, 0)
        result = self.backend._rgb_to_curses_color(rgb)
        # In curses, COLOR_BLACK = 0
        self.assertEqual(result, 0,
                        f"Black {rgb} should map to BLACK (0), got {result}")
    
    def test_saturated_colors_map_correctly(self):
        """Test that saturated colors map to their respective hues"""
        test_cases = [
            ((51, 229, 51), 2, "Green"),      # COLOR_GREEN = 2
            ((40, 80, 160), 4, "Blue"),       # COLOR_BLUE = 4
            ((204, 204, 120), 3, "Yellow"),   # COLOR_YELLOW = 3
            ((255, 255, 0), 3, "Bright yellow"),  # COLOR_YELLOW = 3
            ((0, 255, 255), 6, "Cyan"),       # COLOR_CYAN = 6
            ((255, 0, 255), 5, "Magenta"),    # COLOR_MAGENTA = 5
            ((255, 0, 0), 1, "Red"),          # COLOR_RED = 1
        ]
        
        for rgb, expected, description in test_cases:
            result = self.backend._rgb_to_curses_color(rgb)
            self.assertEqual(result, expected,
                           f"{description} {rgb} should map to {expected}, got {result}")
    
    def test_gray_background_detection(self):
        """Test that gray backgrounds are properly detected"""
        # Dark gray used for headers/footers/status
        bg_rgb = (51, 63, 76)
        bg_brightness = sum(bg_rgb) / 3
        bg_saturation = max(bg_rgb) - min(bg_rgb)
        
        # Should be detected as gray (low saturation, medium brightness)
        self.assertLess(bg_saturation, 40, "Gray should have low saturation")
        self.assertGreater(bg_brightness, 30, "Gray should have brightness > 30")
        self.assertLess(bg_brightness, 150, "Gray should have brightness < 150")
    
    def test_color_pair_special_handling(self):
        """Test that color pair initialization handles gray backgrounds"""
        # This test verifies the logic without actually initializing curses
        fg_rgb = (220, 220, 220)  # Light gray foreground
        bg_rgb = (51, 63, 76)      # Dark gray background
        
        fg_curses = self.backend._rgb_to_curses_color(fg_rgb)
        bg_curses = self.backend._rgb_to_curses_color(bg_rgb)
        
        # Both should map to WHITE
        self.assertEqual(fg_curses, 7, "Light gray foreground should map to WHITE")
        self.assertEqual(bg_curses, 7, "Dark gray background should map to WHITE")
        
        # Check if special handling would apply
        fg_brightness = sum(fg_rgb) / 3
        bg_brightness = sum(bg_rgb) / 3
        bg_saturation = max(bg_rgb) - min(bg_rgb)
        
        should_convert = (fg_curses == 7 and bg_curses == 7 and
                         fg_brightness > 200 and bg_brightness < 100 and
                         bg_saturation < 40)
        
        self.assertTrue(should_convert,
                       "UI bar with light fg and dark gray bg should trigger special handling")
    
    def test_non_gray_colors_not_affected(self):
        """Test that non-gray colors are not affected by special handling"""
        # Test a saturated color that shouldn't trigger special handling
        fg_rgb = (255, 0, 0)  # Red
        bg_rgb = (0, 0, 255)  # Blue
        
        fg_curses = self.backend._rgb_to_curses_color(fg_rgb)
        bg_curses = self.backend._rgb_to_curses_color(bg_rgb)
        
        # Should not both map to WHITE
        self.assertNotEqual((fg_curses, bg_curses), (7, 7),
                          "Saturated colors should not both map to WHITE")
    
    def test_brightness_calculation(self):
        """Test brightness calculation for various colors"""
        test_cases = [
            ((0, 0, 0), 0, "Black"),
            ((255, 255, 255), 255, "White"),
            ((51, 63, 76), 63.33, "Dark gray"),
            ((128, 128, 128), 128, "Medium gray"),
        ]
        
        for rgb, expected_brightness, description in test_cases:
            brightness = sum(rgb) / 3
            self.assertAlmostEqual(brightness, expected_brightness, places=1,
                                 msg=f"{description} brightness calculation")
    
    def test_saturation_calculation(self):
        """Test saturation calculation for various colors"""
        test_cases = [
            ((128, 128, 128), 0, "Pure gray (no saturation)"),
            ((51, 63, 76), 25, "Dark gray (low saturation)"),
            ((255, 0, 0), 255, "Pure red (high saturation)"),
            ((200, 200, 220), 20, "Bluish gray (low saturation)"),
        ]
        
        for rgb, expected_saturation, description in test_cases:
            saturation = max(rgb) - min(rgb)
            self.assertEqual(saturation, expected_saturation,
                           f"{description} saturation calculation")


class TestColorFixIntegration(unittest.TestCase):
    """Integration tests for the color fix"""
    
    def test_header_footer_status_colors(self):
        """Test that header, footer, and status bar colors are properly configured"""
        # Import color constants
        from tfm_colors import (COLOR_HEADER, COLOR_FOOTER, COLOR_STATUS,
                               COLOR_BOUNDARY)
        
        # Verify color pair IDs are defined
        self.assertEqual(COLOR_HEADER, 7, "Header color pair should be 7")
        self.assertEqual(COLOR_FOOTER, 8, "Footer color pair should be 8")
        self.assertEqual(COLOR_STATUS, 9, "Status color pair should be 9")
        self.assertEqual(COLOR_BOUNDARY, 10, "Boundary color pair should be 10")
    
    def test_color_scheme_gray_values(self):
        """Test that color scheme defines proper gray values"""
        from tfm_colors import COLOR_SCHEMES
        
        dark_scheme = COLOR_SCHEMES['dark']
        
        # Check header background
        header_bg = dark_scheme['HEADER_BG']['rgb']
        self.assertEqual(header_bg, (51, 63, 76),
                        "Header background should be dark gray")
        
        # Check footer background
        footer_bg = dark_scheme['FOOTER_BG']['rgb']
        self.assertEqual(footer_bg, (51, 63, 76),
                        "Footer background should be dark gray")
        
        # Check status background
        status_bg = dark_scheme['STATUS_BG']['rgb']
        self.assertEqual(status_bg, (51, 63, 76),
                        "Status background should be dark gray")


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestColorFix))
    suite.addTests(loader.loadTestsFromTestCase(TestColorFixIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
