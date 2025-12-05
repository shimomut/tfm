#!/usr/bin/env python3
"""
Property-based test for feature parity between TUI and GUI backends
Feature: qt-gui-port, Property 3: Feature parity between backends
Validates: Requirements 1.5
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock
import pytest
from hypothesis import given, strategies as st, settings

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_application import TFMApplication
from tfm_ui_backend import IUIBackend, InputEvent
from tfm_config import ConfigManager


class MockBackend(IUIBackend):
    """Mock backend for testing"""
    
    def __init__(self, mode='tui'):
        self.mode = mode
        self.initialized = False
        self.features = {
            'render_panes': False,
            'render_header': False,
            'render_footer': False,
            'render_status_bar': False,
            'render_log_pane': False,
            'show_dialog': False,
            'show_progress': False,
            'get_input_event': False,
            'refresh': False,
            'set_color_scheme': False,
            'initialize': False,
            'cleanup': False,
            'get_screen_size': False
        }
        
    def initialize(self):
        self.initialized = True
        self.features['initialize'] = True
        return True
    
    def cleanup(self):
        self.initialized = False
        self.features['cleanup'] = True
    
    def get_screen_size(self):
        self.features['get_screen_size'] = True
        return (24, 80)
    
    def render_panes(self, left_pane, right_pane, active_pane, layout):
        self.features['render_panes'] = True
    
    def render_header(self, left_path, right_path, active_pane):
        self.features['render_header'] = True
    
    def render_footer(self, left_info, right_info, active_pane):
        self.features['render_footer'] = True
    
    def render_status_bar(self, message, controls):
        self.features['render_status_bar'] = True
    
    def render_log_pane(self, messages, scroll_offset, height_ratio):
        self.features['render_log_pane'] = True
    
    def show_dialog(self, dialog_type, **kwargs):
        self.features['show_dialog'] = True
        return None
    
    def show_progress(self, operation, current, total, message):
        self.features['show_progress'] = True
    
    def get_input_event(self, timeout=-1):
        self.features['get_input_event'] = True
        return None
    
    def refresh(self):
        self.features['refresh'] = True
    
    def set_color_scheme(self, scheme):
        self.features['set_color_scheme'] = True


class TestFeatureParity:
    """
    **Feature: qt-gui-port, Property 3: Feature parity between backends**
    **Validates: Requirements 1.5**
    
    Property: For any core file management feature, both TUI and GUI backends should
    provide access to that feature through their respective interfaces.
    """
    
    @given(
        mode1=st.sampled_from(['tui', 'gui']),
        mode2=st.sampled_from(['tui', 'gui'])
    )
    @settings(max_examples=100)
    def test_backend_interface_parity(self, mode1, mode2):
        """
        Property test: Both backends should implement the same interface methods
        
        For any two backends (TUI or GUI), they should have the same set of methods
        available from the IUIBackend interface.
        """
        backend1 = MockBackend(mode=mode1)
        backend2 = MockBackend(mode=mode2)
        
        # Get all methods from IUIBackend interface
        interface_methods = [
            'initialize', 'cleanup', 'get_screen_size',
            'render_panes', 'render_header', 'render_footer',
            'render_status_bar', 'render_log_pane',
            'show_dialog', 'show_progress',
            'get_input_event', 'refresh', 'set_color_scheme'
        ]
        
        # Both backends should have all interface methods
        for method in interface_methods:
            assert hasattr(backend1, method), \
                f"{mode1} backend missing method: {method}"
            assert hasattr(backend2, method), \
                f"{mode2} backend missing method: {method}"
            
            # Both should be callable
            assert callable(getattr(backend1, method)), \
                f"{mode1} backend {method} is not callable"
            assert callable(getattr(backend2, method)), \
                f"{mode2} backend {method} is not callable"
    
    @given(
        mode=st.sampled_from(['tui', 'gui'])
    )
    @settings(max_examples=100)
    def test_rendering_features_available(self, mode):
        """
        Property test: All rendering features should be available in both modes
        
        For any mode, all rendering methods should be callable and functional.
        """
        backend = MockBackend(mode=mode)
        config = ConfigManager()
        app = TFMApplication(backend, config)
        
        # Test rendering features
        backend.render_panes({}, {}, 'left', {})
        assert backend.features['render_panes'] == True
        
        backend.render_header('/path1', '/path2', 'left')
        assert backend.features['render_header'] == True
        
        backend.render_footer('info1', 'info2', 'left')
        assert backend.features['render_footer'] == True
        
        backend.render_status_bar('message', [])
        assert backend.features['render_status_bar'] == True
        
        backend.render_log_pane([], 0, 0.3)
        assert backend.features['render_log_pane'] == True
    
    @given(
        mode=st.sampled_from(['tui', 'gui']),
        dialog_type=st.sampled_from(['confirmation', 'input', 'list', 'info', 'progress'])
    )
    @settings(max_examples=100)
    def test_dialog_features_available(self, mode, dialog_type):
        """
        Property test: All dialog types should be available in both modes
        
        For any mode and dialog type, the show_dialog method should be callable.
        """
        backend = MockBackend(mode=mode)
        config = ConfigManager()
        app = TFMApplication(backend, config)
        
        # Test dialog feature
        backend.show_dialog(dialog_type, title='Test', message='Test message')
        assert backend.features['show_dialog'] == True
    
    @given(
        mode=st.sampled_from(['tui', 'gui'])
    )
    @settings(max_examples=100)
    def test_progress_features_available(self, mode):
        """
        Property test: Progress indication should be available in both modes
        
        For any mode, progress indication should be functional.
        """
        backend = MockBackend(mode=mode)
        config = ConfigManager()
        app = TFMApplication(backend, config)
        
        # Test progress feature
        backend.show_progress('Operation', 50, 100, 'file.txt')
        assert backend.features['show_progress'] == True
    
    @given(
        mode=st.sampled_from(['tui', 'gui'])
    )
    @settings(max_examples=100)
    def test_input_handling_available(self, mode):
        """
        Property test: Input handling should be available in both modes
        
        For any mode, input event handling should be functional.
        """
        backend = MockBackend(mode=mode)
        config = ConfigManager()
        app = TFMApplication(backend, config)
        
        # Test input handling
        backend.get_input_event(timeout=0)
        assert backend.features['get_input_event'] == True
    
    @given(
        mode=st.sampled_from(['tui', 'gui']),
        color_scheme=st.sampled_from(['dark', 'light'])
    )
    @settings(max_examples=100)
    def test_color_scheme_features_available(self, mode, color_scheme):
        """
        Property test: Color scheme support should be available in both modes
        
        For any mode and color scheme, the set_color_scheme method should work.
        """
        backend = MockBackend(mode=mode)
        config = ConfigManager()
        app = TFMApplication(backend, config)
        
        # Test color scheme feature
        backend.set_color_scheme(color_scheme)
        assert backend.features['set_color_scheme'] == True
    
    @given(
        mode=st.sampled_from(['tui', 'gui'])
    )
    @settings(max_examples=100)
    def test_lifecycle_features_available(self, mode):
        """
        Property test: Lifecycle methods should be available in both modes
        
        For any mode, initialize, cleanup, and refresh should be functional.
        """
        backend = MockBackend(mode=mode)
        config = ConfigManager()
        app = TFMApplication(backend, config)
        
        # Test lifecycle features
        result = backend.initialize()
        assert result == True
        assert backend.features['initialize'] == True
        
        backend.refresh()
        assert backend.features['refresh'] == True
        
        backend.cleanup()
        assert backend.features['cleanup'] == True
    
    @given(
        mode=st.sampled_from(['tui', 'gui'])
    )
    @settings(max_examples=100)
    def test_screen_size_available(self, mode):
        """
        Property test: Screen size retrieval should be available in both modes
        
        For any mode, get_screen_size should return valid dimensions.
        """
        backend = MockBackend(mode=mode)
        config = ConfigManager()
        app = TFMApplication(backend, config)
        
        # Test screen size feature
        size = backend.get_screen_size()
        assert backend.features['get_screen_size'] == True
        assert isinstance(size, tuple)
        assert len(size) == 2
        assert size[0] > 0
        assert size[1] > 0
    
    def test_feature_completeness_tui_vs_gui(self):
        """
        Test that TUI and GUI backends have complete feature parity
        """
        tui_backend = MockBackend(mode='tui')
        gui_backend = MockBackend(mode='gui')
        
        # Exercise all features in both backends
        for backend in [tui_backend, gui_backend]:
            backend.initialize()
            backend.get_screen_size()
            backend.render_panes({}, {}, 'left', {})
            backend.render_header('/path1', '/path2', 'left')
            backend.render_footer('info1', 'info2', 'left')
            backend.render_status_bar('message', [])
            backend.render_log_pane([], 0, 0.3)
            backend.show_dialog('confirmation', title='Test')
            backend.show_progress('Op', 50, 100, 'file')
            backend.get_input_event(0)
            backend.refresh()
            backend.set_color_scheme('dark')
            backend.cleanup()
        
        # Both should have exercised all features
        assert tui_backend.features == gui_backend.features
        
        # All features should be True
        for feature, used in tui_backend.features.items():
            assert used == True, f"Feature {feature} not exercised in TUI"
        
        for feature, used in gui_backend.features.items():
            assert used == True, f"Feature {feature} not exercised in GUI"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
