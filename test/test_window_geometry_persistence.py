"""
Property-based tests for window geometry persistence.

Tests Properties 28 and 29 from the design document:
- Property 28: Window geometry persistence
- Property 29: Window geometry restoration

**Feature: qt-gui-port, Property 28: Window geometry persistence**
**Feature: qt-gui-port, Property 29: Window geometry restoration**
**Validates: Requirements 10.1, 10.2, 10.3**
"""

import sys
import pytest
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint, QSize, QRect
from PySide6.QtTest import QTest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_qt_main_window import TFMMainWindow
from tfm_config import config_manager


# Skip all tests in this file if running in CI or headless environment
pytestmark = pytest.mark.skip(reason="Qt GUI tests require display and may cause segfaults in CI")


@pytest.fixture(scope='module')
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def main_window(qapp):
    """Create a main window for testing."""
    window = TFMMainWindow()
    yield window
    window.close()


class TestWindowGeometryPersistence:
    """Test window geometry persistence properties."""
    
    @given(
        width=st.integers(min_value=800, max_value=2000),
        height=st.integers(min_value=600, max_value=1500)
    )
    @settings(max_examples=10, deadline=5000)
    def test_property_28_window_size_persistence(self, qapp, width, height):
        """
        Property 28: Window geometry persistence
        
        For any window resize operation, the new dimensions should be saved
        to the configuration file.
        
        **Feature: qt-gui-port, Property 28: Window geometry persistence**
        **Validates: Requirements 10.1, 10.2**
        """
        # Create window
        window = TFMMainWindow()
        
        try:
            # Resize window
            window.resize(width, height)
            
            # Process events to ensure resize is handled
            QTest.qWait(100)
            qapp.processEvents()
            
            # Wait for debounced save (timer is 500ms)
            QTest.qWait(600)
            qapp.processEvents()
            
            # Trigger immediate save by closing
            window._save_geometry_now()
            
            # Reload config to get saved values
            config = config_manager.reload_config()
            
            # Verify size was saved
            assert hasattr(config, 'GUI_WINDOW_WIDTH'), "GUI_WINDOW_WIDTH not in config"
            assert hasattr(config, 'GUI_WINDOW_HEIGHT'), "GUI_WINDOW_HEIGHT not in config"
            
            # Allow small tolerance for window manager adjustments
            assert abs(config.GUI_WINDOW_WIDTH - width) <= 10, \
                f"Width not saved correctly: expected {width}, got {config.GUI_WINDOW_WIDTH}"
            assert abs(config.GUI_WINDOW_HEIGHT - height) <= 10, \
                f"Height not saved correctly: expected {height}, got {config.GUI_WINDOW_HEIGHT}"
            
        finally:
            window.close()
    
    @given(
        x=st.integers(min_value=0, max_value=1000),
        y=st.integers(min_value=0, max_value=800)
    )
    @settings(max_examples=10, deadline=5000)
    def test_property_28_window_position_persistence(self, qapp, x, y):
        """
        Property 28: Window geometry persistence
        
        For any window move operation, the new position should be saved
        to the configuration file.
        
        **Feature: qt-gui-port, Property 28: Window geometry persistence**
        **Validates: Requirements 10.1, 10.2**
        """
        # Create window
        window = TFMMainWindow()
        
        try:
            # Move window
            window.move(x, y)
            
            # Process events to ensure move is handled
            QTest.qWait(100)
            qapp.processEvents()
            
            # Wait for debounced save (timer is 500ms)
            QTest.qWait(600)
            qapp.processEvents()
            
            # Trigger immediate save by closing
            window._save_geometry_now()
            
            # Reload config to get saved values
            config = config_manager.reload_config()
            
            # Verify position was saved
            assert hasattr(config, 'GUI_WINDOW_X'), "GUI_WINDOW_X not in config"
            assert hasattr(config, 'GUI_WINDOW_Y'), "GUI_WINDOW_Y not in config"
            
            # Allow small tolerance for window manager adjustments
            assert abs(config.GUI_WINDOW_X - x) <= 10, \
                f"X position not saved correctly: expected {x}, got {config.GUI_WINDOW_X}"
            assert abs(config.GUI_WINDOW_Y - y) <= 10, \
                f"Y position not saved correctly: expected {y}, got {config.GUI_WINDOW_Y}"
            
        finally:
            window.close()
    
    @given(
        width=st.integers(min_value=800, max_value=2000),
        height=st.integers(min_value=600, max_value=1500),
        x=st.integers(min_value=0, max_value=1000),
        y=st.integers(min_value=0, max_value=800)
    )
    @settings(max_examples=10, deadline=5000)
    def test_property_29_window_geometry_restoration(self, qapp, width, height, x, y):
        """
        Property 29: Window geometry restoration
        
        For any GUI launch with saved window geometry, the window should be
        restored to the saved size and position.
        
        **Feature: qt-gui-port, Property 29: Window geometry restoration**
        **Validates: Requirements 10.3**
        """
        # First, save geometry
        config_manager.save_gui_geometry(width, height, x, y)
        
        # Create new window (should restore saved geometry)
        window = TFMMainWindow()
        
        try:
            # Process events to ensure window is fully initialized
            QTest.qWait(100)
            qapp.processEvents()
            
            # Verify size was restored (allow tolerance for window manager)
            actual_width = window.width()
            actual_height = window.height()
            
            assert abs(actual_width - width) <= 10, \
                f"Width not restored correctly: expected {width}, got {actual_width}"
            assert abs(actual_height - height) <= 10, \
                f"Height not restored correctly: expected {height}, got {actual_height}"
            
            # Verify position was restored (allow tolerance for window manager)
            actual_x = window.x()
            actual_y = window.y()
            
            assert abs(actual_x - x) <= 10, \
                f"X position not restored correctly: expected {x}, got {actual_x}"
            assert abs(actual_y - y) <= 10, \
                f"Y position not restored correctly: expected {y}, got {actual_y}"
            
        finally:
            window.close()
    
    def test_property_29_default_geometry_when_no_config(self, qapp):
        """
        Property 29: Window geometry restoration
        
        When no saved configuration exists, the window should use default
        geometry and center on screen.
        
        **Feature: qt-gui-port, Property 29: Window geometry restoration**
        **Validates: Requirements 10.3, 10.4**
        """
        # Save current config values
        config = config_manager.get_config()
        original_width = getattr(config, 'GUI_WINDOW_WIDTH', 1200)
        original_height = getattr(config, 'GUI_WINDOW_HEIGHT', 800)
        original_x = getattr(config, 'GUI_WINDOW_X', None)
        original_y = getattr(config, 'GUI_WINDOW_Y', None)
        
        try:
            # Set config to None values (simulating no saved config)
            config_manager.save_gui_geometry(1200, 800, None, None)
            
            # Create window
            window = TFMMainWindow()
            
            try:
                # Process events
                QTest.qWait(100)
                qapp.processEvents()
                
                # Verify default size is used
                assert window.width() == 1200, "Default width not used"
                assert window.height() == 800, "Default height not used"
                
                # Verify window is centered (position should be calculated to center)
                screen_geometry = window.screen().availableGeometry()
                expected_x = (screen_geometry.width() - 1200) // 2
                expected_y = (screen_geometry.height() - 800) // 2
                
                # Allow tolerance for window manager
                assert abs(window.x() - expected_x) <= 50, \
                    f"Window not centered horizontally: expected ~{expected_x}, got {window.x()}"
                assert abs(window.y() - expected_y) <= 50, \
                    f"Window not centered vertically: expected ~{expected_y}, got {window.y()}"
                
            finally:
                window.close()
        
        finally:
            # Restore original config
            if original_x is not None and original_y is not None:
                config_manager.save_gui_geometry(
                    original_width, original_height, original_x, original_y
                )
    
    def test_property_29_off_screen_position_handling(self, qapp):
        """
        Property 29: Window geometry restoration
        
        When saved position is off-screen, the window should be centered
        on screen instead.
        
        **Feature: qt-gui-port, Property 29: Window geometry restoration**
        **Validates: Requirements 10.5**
        """
        # Save off-screen position
        config_manager.save_gui_geometry(1200, 800, -5000, -5000)
        
        # Create window
        window = TFMMainWindow()
        
        try:
            # Process events
            QTest.qWait(100)
            qapp.processEvents()
            
            # Verify window is on screen
            screen_geometry = window.screen().availableGeometry()
            window_rect = window.frameGeometry()
            
            # Window should intersect with screen (at least partially visible)
            assert screen_geometry.intersects(window_rect), \
                "Window is completely off-screen"
            
            # Window should be reasonably centered (not at saved off-screen position)
            assert window.x() > -1000, "Window X position is still off-screen"
            assert window.y() > -1000, "Window Y position is still off-screen"
            assert window.x() < screen_geometry.width(), \
                "Window X position is beyond screen width"
            assert window.y() < screen_geometry.height(), \
                "Window Y position is beyond screen height"
            
        finally:
            window.close()


class TestWindowGeometryEdgeCases:
    """Test edge cases for window geometry handling."""
    
    def test_minimum_window_size_enforced(self, qapp):
        """Verify minimum window size is enforced."""
        window = TFMMainWindow()
        
        try:
            # Try to resize below minimum
            window.resize(100, 100)
            
            # Process events
            QTest.qWait(100)
            qapp.processEvents()
            
            # Verify minimum size is enforced
            assert window.width() >= 800, "Minimum width not enforced"
            assert window.height() >= 600, "Minimum height not enforced"
            
        finally:
            window.close()
    
    def test_geometry_save_on_close(self, qapp):
        """Verify geometry is saved when window is closed."""
        window = TFMMainWindow()
        
        # Resize window
        window.resize(1000, 700)
        window.move(100, 100)
        
        # Process events
        QTest.qWait(100)
        qapp.processEvents()
        
        # Close window (should trigger immediate save)
        window.close()
        
        # Reload config
        config = config_manager.reload_config()
        
        # Verify geometry was saved
        assert abs(config.GUI_WINDOW_WIDTH - 1000) <= 10, \
            "Width not saved on close"
        assert abs(config.GUI_WINDOW_HEIGHT - 700) <= 10, \
            "Height not saved on close"
        assert abs(config.GUI_WINDOW_X - 100) <= 10, \
            "X position not saved on close"
        assert abs(config.GUI_WINDOW_Y - 100) <= 10, \
            "Y position not saved on close"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
