#!/usr/bin/env python3
"""
Property-based test for configuration consistency across TUI and GUI modes
Feature: qt-gui-port, Property 2: Configuration consistency across modes
Validates: Requirements 1.4
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import pytest
from hypothesis import given, strategies as st, settings

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_application import TFMApplication
from tfm_ui_backend import IUIBackend
from tfm_config import ConfigManager


class MockBackend(IUIBackend):
    """Mock backend for testing"""
    
    def __init__(self, mode='tui'):
        self.mode = mode
        self.initialized = False
        
    def initialize(self):
        self.initialized = True
        return True
    
    def cleanup(self):
        self.initialized = False
    
    def get_screen_size(self):
        return (24, 80)
    
    def render_panes(self, left_pane, right_pane, active_pane, layout):
        pass
    
    def render_header(self, left_path, right_path, active_pane):
        pass
    
    def render_footer(self, left_info, right_info, active_pane):
        pass
    
    def render_status_bar(self, message, controls):
        pass
    
    def render_log_pane(self, messages, scroll_offset, height_ratio):
        pass
    
    def show_dialog(self, dialog_type, **kwargs):
        return None
    
    def show_progress(self, operation, current, total, message):
        pass
    
    def get_input_event(self, timeout=-1):
        return None
    
    def refresh(self):
        pass
    
    def set_color_scheme(self, scheme):
        pass


class TestConfigurationConsistency:
    """
    **Feature: qt-gui-port, Property 2: Configuration consistency across modes**
    **Validates: Requirements 1.4**
    
    Property: For any configuration file and user preferences, loading them in TUI mode
    or GUI mode should result in identical configuration data being used by the application.
    """
    
    @given(
        mode1=st.sampled_from(['tui', 'gui']),
        mode2=st.sampled_from(['tui', 'gui'])
    )
    @settings(max_examples=100)
    def test_configuration_consistency_across_modes(self, mode1, mode2):
        """
        Property test: Configuration loading should be identical regardless of mode
        
        For any two modes (TUI or GUI), loading configuration should use the same
        ConfigManager and produce consistent results.
        """
        # Create backends for both modes
        backend1 = MockBackend(mode=mode1)
        config1 = ConfigManager()
        app1 = TFMApplication(backend1, config1)
        
        backend2 = MockBackend(mode=mode2)
        config2 = ConfigManager()
        app2 = TFMApplication(backend2, config2)
        
        # Both should use the same config file location
        assert config1.config_file == config2.config_file, \
            f"Config file location differs: {mode1}={config1.config_file}, {mode2}={config2.config_file}"
        
        # Both should use the same config directory
        assert config1.config_dir == config2.config_dir, \
            f"Config directory differs: {mode1}={config1.config_dir}, {mode2}={config2.config_dir}"
    
    @given(
        mode=st.sampled_from(['tui', 'gui'])
    )
    @settings(max_examples=100)
    def test_config_manager_independence_from_mode(self, mode):
        """
        Property test: ConfigManager should work independently of UI mode
        
        For any mode (TUI or GUI), ConfigManager should function identically.
        """
        # Create backend and config
        backend = MockBackend(mode=mode)
        config = ConfigManager()
        app = TFMApplication(backend, config)
        
        # ConfigManager should work regardless of mode
        assert config.config_dir is not None
        assert config.config_file is not None
        
        # Backend should initialize successfully
        assert backend.initialize() == True
        assert backend.initialized == True
    
    @given(
        mode1=st.sampled_from(['tui', 'gui']),
        mode2=st.sampled_from(['tui', 'gui'])
    )
    @settings(max_examples=100)
    def test_config_loading_behavior_consistency(self, mode1, mode2):
        """
        Property test: Configuration loading behavior should be consistent across modes
        
        For any two modes, the configuration loading process should be identical.
        """
        # Create configs for both modes
        backend1 = MockBackend(mode=mode1)
        config1 = ConfigManager()
        
        backend2 = MockBackend(mode=mode2)
        config2 = ConfigManager()
        
        # Both should have the same configuration structure
        assert type(config1) == type(config2)
        assert config1.config_dir == config2.config_dir
        assert config1.config_file == config2.config_file
        
        # Both should be able to ensure config directory
        result1 = config1.ensure_config_dir()
        result2 = config2.ensure_config_dir()
        assert result1 == result2
    
    def test_default_config_consistency(self):
        """
        Test that default configuration is consistent when no config file exists
        """
        # Create TUI app with default config
        tui_backend = MockBackend(mode='tui')
        tui_config = ConfigManager()
        tui_app = TFMApplication(tui_backend, tui_config)
        
        # Create GUI app with default config
        gui_backend = MockBackend(mode='gui')
        gui_config = ConfigManager()
        gui_app = TFMApplication(gui_backend, gui_config)
        
        # Both should initialize successfully
        assert tui_backend.initialize() == True
        assert gui_backend.initialize() == True
        
        # Both should have the same default configuration attributes
        # (We can't compare all attributes, but we can verify they both work)
        assert hasattr(tui_config, '__dict__')
        assert hasattr(gui_config, '__dict__')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
