"""
Property-Based Tests for Color Scheme Consistency

Tests Property 32: Color scheme consistency
Validates: Requirements 12.2

These tests verify that color definitions are consistent between TUI and GUI modes.
"""

import pytest
from hypothesis import given, strategies as st, assume
from PySide6.QtGui import QColor

# Import color modules
from src.tfm_colors import COLOR_SCHEMES, get_current_rgb_colors
from src.tfm_qt_colors import get_qt_colors, rgb_to_qcolor, get_file_color


# Mark all tests in this module to be skipped (Qt tests may segfault in CI)
pytestmark = pytest.mark.skip(reason="Qt GUI tests require display and may segfault in CI")


class TestColorSchemeConsistency:
    """Test color scheme consistency between TUI and GUI modes."""
    
    @given(
        scheme=st.sampled_from(['dark', 'light'])
    )
    def test_property_32_all_tui_colors_available_in_qt(self, scheme):
        """
        Property 32: Color scheme consistency
        
        For any color definition used in TUI mode, the same color definition 
        should be available in GUI mode.
        
        Validates: Requirements 12.2
        """
        # Get TUI colors for the scheme
        tui_colors = COLOR_SCHEMES[scheme]
        
        # Get Qt colors for the scheme
        qt_colors = get_qt_colors(scheme)
        
        # Verify all TUI color names are available in Qt
        for color_name in tui_colors.keys():
            assert color_name in qt_colors, \
                f"Color '{color_name}' from TUI scheme '{scheme}' not found in Qt colors"
    
    @given(
        scheme=st.sampled_from(['dark', 'light']),
        color_name=st.sampled_from([
            'DIRECTORY_FG', 'EXECUTABLE_FG', 'SELECTED_BG', 'REGULAR_FILE_FG',
            'HEADER_BG', 'FOOTER_BG', 'DEFAULT_FG', 'DEFAULT_BG'
        ])
    )
    def test_property_32_rgb_values_match(self, scheme, color_name):
        """
        Property 32: Color scheme consistency - RGB values
        
        For any color definition, the RGB values should match between TUI and GUI modes.
        
        Validates: Requirements 12.2
        """
        # Get TUI color RGB
        tui_color_def = COLOR_SCHEMES[scheme][color_name]
        tui_rgb = tui_color_def['rgb']
        
        # Get Qt color
        qt_colors = get_qt_colors(scheme)
        qt_color = qt_colors[color_name]
        
        # Verify RGB values match
        assert qt_color.red() == tui_rgb[0], \
            f"Red component mismatch for {color_name} in {scheme}: Qt={qt_color.red()}, TUI={tui_rgb[0]}"
        assert qt_color.green() == tui_rgb[1], \
            f"Green component mismatch for {color_name} in {scheme}: Qt={qt_color.green()}, TUI={tui_rgb[1]}"
        assert qt_color.blue() == tui_rgb[2], \
            f"Blue component mismatch for {color_name} in {scheme}: Qt={qt_color.blue()}, TUI={tui_rgb[2]}"
    
    @given(
        r=st.integers(min_value=0, max_value=255),
        g=st.integers(min_value=0, max_value=255),
        b=st.integers(min_value=0, max_value=255)
    )
    def test_property_32_rgb_to_qcolor_conversion(self, r, g, b):
        """
        Property 32: Color scheme consistency - RGB conversion
        
        For any RGB tuple, conversion to QColor should preserve the values.
        
        Validates: Requirements 12.2
        """
        rgb = (r, g, b)
        qcolor = rgb_to_qcolor(rgb)
        
        assert qcolor.red() == r
        assert qcolor.green() == g
        assert qcolor.blue() == b
    
    @given(
        scheme=st.sampled_from(['dark', 'light']),
        file_type=st.sampled_from(['directory', 'executable', 'regular', 'symlink'])
    )
    def test_property_33_file_type_coloring_consistency(self, scheme, file_type):
        """
        Property 33: File type coloring
        
        For any file type, files of that type should be displayed with 
        consistent coloring based on the configured color scheme.
        
        Validates: Requirements 12.3
        """
        # Get color for file type
        color = get_file_color(file_type, scheme)
        
        # Verify color is a valid QColor
        assert isinstance(color, QColor)
        assert color.isValid()
        
        # Get expected color from scheme
        qt_colors = get_qt_colors(scheme)
        
        if file_type == 'directory':
            expected = qt_colors.get('DIRECTORY_FG')
        elif file_type == 'executable':
            expected = qt_colors.get('EXECUTABLE_FG')
        elif file_type == 'regular':
            expected = qt_colors.get('REGULAR_FILE_FG')
        elif file_type == 'symlink':
            # Symlinks use a hardcoded cyan color
            expected = QColor(0, 255, 255)
        
        # Verify colors match
        if expected:
            assert color.red() == expected.red()
            assert color.green() == expected.green()
            assert color.blue() == expected.blue()
    
    @given(
        scheme=st.sampled_from(['dark', 'light'])
    )
    def test_property_32_color_scheme_completeness(self, scheme):
        """
        Property 32: Color scheme consistency - Completeness
        
        For any color scheme, all required colors should be defined.
        
        Validates: Requirements 12.2
        """
        required_colors = [
            'DIRECTORY_FG', 'EXECUTABLE_FG', 'SELECTED_BG', 'REGULAR_FILE_FG',
            'HEADER_BG', 'FOOTER_BG', 'STATUS_BG', 'DEFAULT_FG', 'DEFAULT_BG'
        ]
        
        qt_colors = get_qt_colors(scheme)
        
        for color_name in required_colors:
            assert color_name in qt_colors, \
                f"Required color '{color_name}' missing from Qt scheme '{scheme}'"
            
            color = qt_colors[color_name]
            assert isinstance(color, QColor)
            assert color.isValid()
    
    def test_property_32_invalid_scheme_fallback(self):
        """
        Property 32: Color scheme consistency - Invalid scheme handling
        
        For any invalid color scheme name, the system should fall back to 'dark'.
        
        Validates: Requirements 12.2
        """
        # Test with invalid scheme name
        qt_colors = get_qt_colors('invalid_scheme')
        
        # Should fall back to dark scheme
        dark_colors = get_qt_colors('dark')
        
        # Verify we got the dark scheme colors
        assert len(qt_colors) == len(dark_colors)
        
        # Check a few key colors match
        for color_name in ['DIRECTORY_FG', 'EXECUTABLE_FG', 'DEFAULT_BG']:
            assert qt_colors[color_name].red() == dark_colors[color_name].red()
            assert qt_colors[color_name].green() == dark_colors[color_name].green()
            assert qt_colors[color_name].blue() == dark_colors[color_name].blue()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
