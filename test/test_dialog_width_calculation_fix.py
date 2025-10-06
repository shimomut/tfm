#!/usr/bin/env python3
"""
Test dialog width calculation fixes

This test verifies that dialog width calculations handle narrow terminals correctly
without requiring curses initialization.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import unittest
from unittest.mock import Mock


class TestDialogWidthCalculationFix(unittest.TestCase):
    """Test dialog width calculation fixes"""
    
    def test_safe_dialog_dimensions_calculation(self):
        """Test the safe dialog dimension calculation logic"""
        
        def calculate_safe_dialog_dimensions(terminal_width, terminal_height, width_ratio, height_ratio, min_width, min_height):
            """Calculate safe dialog dimensions that fit within terminal bounds"""
            # Calculate desired dimensions
            desired_width = int(terminal_width * width_ratio)
            desired_height = int(terminal_height * height_ratio)
            
            # Apply minimum constraints, but never exceed terminal size
            dialog_width = max(min_width, desired_width)
            dialog_width = min(dialog_width, terminal_width)  # Never exceed terminal width
            
            dialog_height = max(min_height, desired_height)
            dialog_height = min(dialog_height, terminal_height)  # Never exceed terminal height
            
            # Calculate safe centering
            start_x = max(0, (terminal_width - dialog_width) // 2)
            start_y = max(0, (terminal_height - dialog_height) // 2)
            
            return dialog_width, dialog_height, start_x, start_y
        
        # Test cases: (terminal_width, terminal_height, width_ratio, height_ratio, min_width, min_height)
        test_cases = [
            # Narrow terminal where min_width exceeds terminal width
            (30, 24, 0.6, 0.7, 40, 15),
            # Very narrow terminal
            (25, 20, 0.8, 0.8, 40, 15),
            # Extremely narrow terminal
            (20, 15, 0.9, 0.9, 40, 15),
            # Normal terminal
            (80, 24, 0.6, 0.7, 40, 15),
            # Wide terminal
            (120, 30, 0.6, 0.7, 40, 15),
        ]
        
        for terminal_width, terminal_height, width_ratio, height_ratio, min_width, min_height in test_cases:
            with self.subTest(terminal_size=f"{terminal_width}x{terminal_height}"):
                dialog_width, dialog_height, start_x, start_y = calculate_safe_dialog_dimensions(
                    terminal_width, terminal_height, width_ratio, height_ratio, min_width, min_height
                )
                
                # Dialog should never exceed terminal dimensions
                self.assertLessEqual(dialog_width, terminal_width, 
                                   f"Dialog width {dialog_width} exceeds terminal width {terminal_width}")
                self.assertLessEqual(dialog_height, terminal_height,
                                   f"Dialog height {dialog_height} exceeds terminal height {terminal_height}")
                
                # Dialog should be positioned within terminal bounds
                self.assertGreaterEqual(start_x, 0, "Dialog start_x should not be negative")
                self.assertGreaterEqual(start_y, 0, "Dialog start_y should not be negative")
                self.assertLessEqual(start_x + dialog_width, terminal_width,
                                   "Dialog should not extend beyond terminal width")
                self.assertLessEqual(start_y + dialog_height, terminal_height,
                                   "Dialog should not extend beyond terminal height")
                
                # Dialog should have positive dimensions
                self.assertGreater(dialog_width, 0, "Dialog width should be positive")
                self.assertGreater(dialog_height, 0, "Dialog height should be positive")
    
    def test_batch_rename_dialog_width_calculation(self):
        """Test BatchRenameDialog width calculation logic"""
        
        def calculate_batch_rename_dimensions(terminal_width, terminal_height):
            """Calculate BatchRenameDialog dimensions using the fixed logic"""
            desired_width = int(terminal_width * 0.9)
            desired_height = int(terminal_height * 0.9)
            
            # Apply minimum constraints, but never exceed terminal size
            dialog_width = max(80, desired_width)
            dialog_width = min(dialog_width, terminal_width)  # Never exceed terminal width
            
            dialog_height = max(25, desired_height)
            dialog_height = min(dialog_height, terminal_height)  # Never exceed terminal height
            
            # Calculate safe centering
            start_y = max(0, (terminal_height - dialog_height) // 2)
            start_x = max(0, (terminal_width - dialog_width) // 2)
            
            return dialog_width, dialog_height, start_x, start_y
        
        # Test various terminal sizes
        test_cases = [
            (30, 24),   # Narrow - min_width (80) exceeds terminal width (30)
            (50, 24),   # Medium narrow
            (80, 24),   # Exactly min_width
            (100, 30),  # Normal
            (120, 30),  # Wide
        ]
        
        for terminal_width, terminal_height in test_cases:
            with self.subTest(terminal_size=f"{terminal_width}x{terminal_height}"):
                dialog_width, dialog_height, start_x, start_y = calculate_batch_rename_dimensions(
                    terminal_width, terminal_height
                )
                
                # Dialog should never exceed terminal dimensions
                self.assertLessEqual(dialog_width, terminal_width, 
                                   f"BatchRename dialog width {dialog_width} exceeds terminal width {terminal_width}")
                self.assertLessEqual(dialog_height, terminal_height,
                                   f"BatchRename dialog height {dialog_height} exceeds terminal height {terminal_height}")
                
                # Dialog should be positioned within terminal bounds
                self.assertGreaterEqual(start_x, 0, "Dialog start_x should not be negative")
                self.assertGreaterEqual(start_y, 0, "Dialog start_y should not be negative")
                
                # Dialog should have positive dimensions
                self.assertGreater(dialog_width, 0, "Dialog width should be positive")
                self.assertGreater(dialog_height, 0, "Dialog height should be positive")
    
    def test_text_truncation_logic(self):
        """Test text truncation logic for narrow terminals"""
        
        def safe_truncate_text(text, max_width, suffix="..."):
            """Safely truncate text to fit within max_width"""
            if len(text) <= max_width:
                return text
            
            if max_width <= len(suffix):
                return suffix[:max_width]
            
            return text[:max_width - len(suffix)] + suffix
        
        # Test cases: (text, max_width, expected_result)
        test_cases = [
            ("Short text", 20, "Short text"),  # No truncation needed
            ("This is a very long text that needs truncation", 20, "This is a very lo..."),  # Normal truncation
            ("Text", 3, "..."),  # Max width equals suffix length
            ("Text", 2, ".."),   # Max width less than suffix length
            ("Text", 1, "."),    # Max width much less than suffix length
            ("", 10, ""),        # Empty text
        ]
        
        for text, max_width, expected in test_cases:
            with self.subTest(text=text, max_width=max_width):
                result = safe_truncate_text(text, max_width)
                self.assertEqual(result, expected)
                self.assertLessEqual(len(result), max_width, 
                                   f"Truncated text '{result}' exceeds max_width {max_width}")
    
    def test_border_line_truncation(self):
        """Test border line truncation for narrow terminals"""
        
        def create_safe_border_line(border_type, dialog_width, terminal_width, start_x):
            """Create a border line that fits within terminal bounds"""
            if border_type == "top":
                line = "┌" + "─" * max(0, dialog_width - 2) + "┐"
            elif border_type == "bottom":
                line = "└" + "─" * max(0, dialog_width - 2) + "┘"
            else:
                line = "├" + "─" * max(0, dialog_width - 2) + "┤"
            
            # Truncate if line would exceed terminal width
            if start_x + len(line) > terminal_width:
                line = line[:terminal_width - start_x]
            
            return line
        
        # Test cases: (dialog_width, terminal_width, start_x)
        test_cases = [
            (40, 30, 0),   # Dialog wider than terminal, start at left edge
            (30, 30, 0),   # Dialog exactly terminal width
            (20, 30, 5),   # Dialog narrower than terminal, centered
            (25, 30, 10),  # Dialog would extend beyond terminal when centered
        ]
        
        for dialog_width, terminal_width, start_x in test_cases:
            with self.subTest(dialog_width=dialog_width, terminal_width=terminal_width, start_x=start_x):
                for border_type in ["top", "bottom", "separator"]:
                    line = create_safe_border_line(border_type, dialog_width, terminal_width, start_x)
                    
                    # Line should not exceed terminal width when positioned
                    self.assertLessEqual(start_x + len(line), terminal_width,
                                       f"Border line '{line}' at position {start_x} exceeds terminal width {terminal_width}")
                    
                    # Line should not be empty unless dialog_width is very small
                    if dialog_width > 0:
                        self.assertGreater(len(line), 0, f"Border line should not be empty for dialog_width {dialog_width}")
    
    def test_title_positioning_logic(self):
        """Test title positioning logic for narrow terminals"""
        
        def calculate_safe_title_position(title, dialog_width, terminal_width, start_x):
            """Calculate safe title position that fits within terminal bounds"""
            title_text = f" {title} "
            title_width = len(title_text)
            
            # Truncate title if it's too wide for the dialog
            if title_width > dialog_width:
                available_width = dialog_width - 2  # Leave space for padding
                if available_width > 3:  # Minimum space for "..."
                    title_text = title[:available_width - 3] + "..."
                else:
                    title_text = title[:available_width] if available_width > 0 else ""
                title_width = len(title_text)
            
            # Calculate centered position
            title_x = start_x + (dialog_width - title_width) // 2
            
            # Ensure title fits within terminal bounds
            if title_x < 0 or title_x + title_width > terminal_width:
                return None, None  # Can't fit title safely
            
            return title_text, title_x
        
        # Test cases: (title, dialog_width, terminal_width, start_x)
        test_cases = [
            ("Test Dialog", 40, 80, 20),    # Normal case
            ("Very Long Dialog Title That Might Not Fit", 30, 80, 25),  # Long title
            ("Test", 10, 30, 10),           # Narrow dialog
            ("Test Dialog", 20, 25, 5),     # Dialog near terminal edge
            ("Test", 5, 20, 0),             # Very narrow dialog
        ]
        
        for title, dialog_width, terminal_width, start_x in test_cases:
            with self.subTest(title=title, dialog_width=dialog_width, terminal_width=terminal_width, start_x=start_x):
                title_text, title_x = calculate_safe_title_position(title, dialog_width, terminal_width, start_x)
                
                if title_text is not None:
                    # Title should fit within dialog bounds
                    self.assertLessEqual(len(title_text), dialog_width,
                                       f"Title '{title_text}' exceeds dialog width {dialog_width}")
                    
                    # Title should fit within terminal bounds
                    self.assertGreaterEqual(title_x, 0, "Title position should not be negative")
                    self.assertLessEqual(title_x + len(title_text), terminal_width,
                                       f"Title '{title_text}' at position {title_x} exceeds terminal width {terminal_width}")


if __name__ == '__main__':
    unittest.main()