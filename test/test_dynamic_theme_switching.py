"""
Property-Based Tests for Dynamic Theme Switching

Tests Property 35: Dynamic theme switching
Validates: Requirements 12.5

These tests verify that theme changes update the GUI appearance immediately
without requiring an application restart.
"""

import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent.parent / 'src'
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import pytest
from hypothesis import given, strategies as st
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Import modules
from tfm_qt_backend import QtBackend
from tfm_qt_colors import get_qt_colors, apply_color_scheme


# Mark all tests in this module to be skipped (Qt tests may segfault in CI)
pytestmark = pytest.mark.skip(reason="Qt GUI tests require display and may segfault in CI")


class TestDynamicThemeSwitching:
    """Test dynamic theme switching in Qt GUI."""
    
    @given(
        initial_scheme=st.sampled_from(['dark', 'light']),
        new_scheme=st.sampled_from(['dark', 'light'])
    )
    def test_property_35_theme_switch_updates_backend(self, initial_scheme, new_scheme, qapp):
        """
        Property 35: Dynamic theme switching - Backend update
        
        For any theme change operation, the backend should update its color scheme.
        
        Validates: Requirements 12.5
        """
        # Create Qt backend
        backend = QtBackend(qapp)
        backend.color_scheme = initial_scheme
        
        # Switch theme
        backend.set_color_scheme(new_scheme)
        
        # Verify backend color scheme updated
        assert backend.color_scheme == new_scheme
    
    @given(
        scheme=st.sampled_from(['dark', 'light'])
    )
    def test_property_35_apply_color_scheme_updates_stylesheet(self, scheme, qapp):
        """
        Property 35: Dynamic theme switching - Stylesheet update
        
        For any theme change, the application stylesheet should be updated.
        
        Validates: Requirements 12.5
        """
        # Apply color scheme
        apply_color_scheme(qapp, scheme)
        
        # Verify stylesheet was set (not empty)
        stylesheet = qapp.styleSheet()
        assert stylesheet is not None
        assert len(stylesheet) > 0
        
        # Verify stylesheet contains scheme-specific colors
        colors = get_qt_colors(scheme)
        default_bg = colors.get('DEFAULT_BG')
        
        # Stylesheet should contain the background color
        assert default_bg.name() in stylesheet
    
    @given(
        initial_scheme=st.sampled_from(['dark', 'light']),
        new_scheme=st.sampled_from(['dark', 'light'])
    )
    def test_property_35_theme_switch_no_restart_required(self, initial_scheme, new_scheme, qapp):
        """
        Property 35: Dynamic theme switching - No restart required
        
        For any theme change, the application should not require a restart.
        The change should be immediate.
        
        Validates: Requirements 12.5
        """
        # Apply initial scheme
        apply_color_scheme(qapp, initial_scheme)
        initial_stylesheet = qapp.styleSheet()
        
        # Switch to new scheme
        apply_color_scheme(qapp, new_scheme)
        new_stylesheet = qapp.styleSheet()
        
        # Verify stylesheet changed (unless schemes are the same)
        if initial_scheme != new_scheme:
            assert initial_stylesheet != new_stylesheet
        else:
            # Same scheme should produce same stylesheet
            assert initial_stylesheet == new_stylesheet
    
    @given(
        scheme=st.sampled_from(['dark', 'light'])
    )
    def test_property_35_color_scheme_affects_all_widgets(self, scheme, qapp):
        """
        Property 35: Dynamic theme switching - All widgets affected
        
        For any theme change, all widget types should be styled consistently.
        
        Validates: Requirements 12.5
        """
        # Apply color scheme
        apply_color_scheme(qapp, scheme)
        stylesheet = qapp.styleSheet()
        
        # Verify stylesheet includes styling for all major widget types
        required_widgets = [
            'QMainWindow',
            'QTableWidget',
            'QDialog',
            'QPushButton',
            'QLineEdit',
            'QProgressBar',
            'QMenuBar',
            'QMenu',
            'QToolBar',
            'QStatusBar'
        ]
        
        for widget_type in required_widgets:
            assert widget_type in stylesheet, \
                f"Stylesheet missing styling for {widget_type}"
    
    @given(
        scheme=st.sampled_from(['dark', 'light'])
    )
    def test_property_35_theme_colors_are_valid(self, scheme, qapp):
        """
        Property 35: Dynamic theme switching - Valid colors
        
        For any theme, all colors should be valid QColor objects.
        
        Validates: Requirements 12.5
        """
        colors = get_qt_colors(scheme)
        
        # Verify all colors are valid
        for color_name, color in colors.items():
            assert color.isValid(), \
                f"Color '{color_name}' in scheme '{scheme}' is not valid"
            
            # Verify RGB components are in valid range
            assert 0 <= color.red() <= 255
            assert 0 <= color.green() <= 255
            assert 0 <= color.blue() <= 255
    
    def test_property_35_multiple_theme_switches(self, qapp):
        """
        Property 35: Dynamic theme switching - Multiple switches
        
        The application should handle multiple theme switches without issues.
        
        Validates: Requirements 12.5
        """
        schemes = ['dark', 'light', 'dark', 'light', 'dark']
        
        for scheme in schemes:
            # Apply scheme
            apply_color_scheme(qapp, scheme)
            
            # Verify stylesheet is set
            stylesheet = qapp.styleSheet()
            assert stylesheet is not None
            assert len(stylesheet) > 0
            
            # Verify colors are correct
            colors = get_qt_colors(scheme)
            default_bg = colors.get('DEFAULT_BG')
            assert default_bg.name() in stylesheet


@pytest.fixture
def qapp():
    """Create QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit the app as it may be shared across tests


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
