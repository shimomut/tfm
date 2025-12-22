#!/usr/bin/env python3
"""
Test configuration system backend settings for TTK migration.

Tests:
1. Default backend configuration
2. Backend validation
3. Desktop mode settings
4. Configuration loading with backend settings
5. Backend preference persistence
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_config import ConfigManager, DefaultConfig


def test_default_backend_config():
    """Test that default configuration includes backend settings"""
    config = DefaultConfig()
    
    # Check backend settings exist
    assert hasattr(config, 'PREFERRED_BACKEND'), "DefaultConfig should have PREFERRED_BACKEND"
    assert config.PREFERRED_BACKEND == 'curses', "Default backend should be 'curses'"
    
    # Check desktop mode settings exist
    assert hasattr(config, 'DESKTOP_FONT_NAME'), "DefaultConfig should have DESKTOP_FONT_NAME"
    assert hasattr(config, 'DESKTOP_FONT_SIZE'), "DefaultConfig should have DESKTOP_FONT_SIZE"
    assert hasattr(config, 'DESKTOP_WINDOW_WIDTH'), "DefaultConfig should have DESKTOP_WINDOW_WIDTH"
    assert hasattr(config, 'DESKTOP_WINDOW_HEIGHT'), "DefaultConfig should have DESKTOP_WINDOW_HEIGHT"
    
    # Check default values
    assert config.DESKTOP_FONT_NAME == ['Menlo', 'Monaco', 'Courier', 'Osaka-Mono', 'Hiragino Sans GB'], "Default font list should include cascade fonts"
    assert config.DESKTOP_FONT_SIZE == 12, "Default font size should be 12"
    assert config.DESKTOP_WINDOW_WIDTH == 1200, "Default window width should be 1200"
    assert config.DESKTOP_WINDOW_HEIGHT == 800, "Default window height should be 800"
    
    print("✓ Default backend configuration test passed")


def test_backend_validation():
    """Test backend validation in ConfigManager"""
    manager = ConfigManager()
    
    # Test valid backend values
    class ValidConfig:
        PREFERRED_BACKEND = 'curses'
    
    errors = manager.validate_config(ValidConfig())
    assert len(errors) == 0, f"Valid 'curses' backend should have no errors, got: {errors}"
    
    ValidConfig.PREFERRED_BACKEND = 'coregraphics'
    errors = manager.validate_config(ValidConfig())
    assert len(errors) == 0, f"Valid 'coregraphics' backend should have no errors, got: {errors}"
    
    # Test invalid backend value
    class InvalidConfig:
        PREFERRED_BACKEND = 'invalid'
    
    errors = manager.validate_config(InvalidConfig())
    assert len(errors) > 0, "Invalid backend should produce validation error"
    assert any('PREFERRED_BACKEND' in err for err in errors), "Error should mention PREFERRED_BACKEND"
    
    print("✓ Backend validation test passed")


def test_desktop_settings_validation():
    """Test desktop mode settings validation"""
    manager = ConfigManager()
    
    # Test valid desktop settings with font list
    class ValidDesktopConfig:
        DESKTOP_FONT_NAME = ['Monaco', 'Menlo', 'Courier']
        DESKTOP_FONT_SIZE = 14
        DESKTOP_WINDOW_WIDTH = 1200
        DESKTOP_WINDOW_HEIGHT = 800
    
    errors = manager.validate_config(ValidDesktopConfig())
    assert len(errors) == 0, f"Valid desktop settings should have no errors, got: {errors}"
    
    # Test valid desktop settings with single font string (backward compatibility)
    class ValidDesktopConfigString:
        DESKTOP_FONT_NAME = 'Monaco'
        DESKTOP_FONT_SIZE = 14
    
    errors = manager.validate_config(ValidDesktopConfigString())
    assert len(errors) == 0, f"Valid desktop settings with string font should have no errors, got: {errors}"
    
    # Test invalid font name (empty string)
    class InvalidFontNameEmpty:
        DESKTOP_FONT_NAME = ''
    
    errors = manager.validate_config(InvalidFontNameEmpty())
    assert len(errors) > 0, "Empty font name should produce validation error"
    assert any('DESKTOP_FONT_NAME' in err for err in errors), "Error should mention DESKTOP_FONT_NAME"
    
    # Test invalid font name (empty list)
    class InvalidFontNameEmptyList:
        DESKTOP_FONT_NAME = []
    
    errors = manager.validate_config(InvalidFontNameEmptyList())
    assert len(errors) > 0, "Empty font name list should produce validation error"
    assert any('DESKTOP_FONT_NAME' in err for err in errors), "Error should mention DESKTOP_FONT_NAME"
    
    # Test invalid font name (list with empty strings)
    class InvalidFontNameListWithEmpty:
        DESKTOP_FONT_NAME = ['Monaco', '', 'Courier']
    
    errors = manager.validate_config(InvalidFontNameListWithEmpty())
    assert len(errors) > 0, "Font name list with empty strings should produce validation error"
    assert any('DESKTOP_FONT_NAME' in err for err in errors), "Error should mention DESKTOP_FONT_NAME"
    
    # Test invalid font name (wrong type)
    class InvalidFontNameType:
        DESKTOP_FONT_NAME = 123
    
    errors = manager.validate_config(InvalidFontNameType())
    assert len(errors) > 0, "Invalid font name type should produce validation error"
    assert any('DESKTOP_FONT_NAME' in err for err in errors), "Error should mention DESKTOP_FONT_NAME"
    
    # Test invalid font size (too small)
    class InvalidFontSizeSmall:
        DESKTOP_FONT_SIZE = 5
    
    errors = manager.validate_config(InvalidFontSizeSmall())
    assert len(errors) > 0, "Font size < 8 should produce validation error"
    assert any('DESKTOP_FONT_SIZE' in err for err in errors), "Error should mention DESKTOP_FONT_SIZE"
    
    # Test invalid font size (too large)
    class InvalidFontSizeLarge:
        DESKTOP_FONT_SIZE = 100
    
    errors = manager.validate_config(InvalidFontSizeLarge())
    assert len(errors) > 0, "Font size > 72 should produce validation error"
    
    # Test invalid window dimensions
    class InvalidWindowSize:
        DESKTOP_WINDOW_WIDTH = 200
        DESKTOP_WINDOW_HEIGHT = 100
    
    errors = manager.validate_config(InvalidWindowSize())
    assert len(errors) >= 2, "Invalid window dimensions should produce validation errors"
    assert any('DESKTOP_WINDOW_WIDTH' in err for err in errors), "Error should mention DESKTOP_WINDOW_WIDTH"
    assert any('DESKTOP_WINDOW_HEIGHT' in err for err in errors), "Error should mention DESKTOP_WINDOW_HEIGHT"
    
    print("✓ Desktop settings validation test passed")


def test_config_loading_with_backend():
    """Test that configuration loading works with backend settings"""
    # Create a temporary config directory
    temp_dir = tempfile.mkdtemp()
    config_dir = Path(temp_dir) / '.tfm'
    config_file = config_dir / 'config.py'
    
    try:
        # Create config directory
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Write a test config file with backend settings
        config_content = '''
class Config:
    """Test configuration"""
    
    # Backend settings
    PREFERRED_BACKEND = 'coregraphics'
    DESKTOP_FONT_NAME = ['Monaco', 'Menlo']
    DESKTOP_FONT_SIZE = 16
    DESKTOP_WINDOW_WIDTH = 1400
    DESKTOP_WINDOW_HEIGHT = 900
    
    # Other settings
    SHOW_HIDDEN_FILES = True
    COLOR_SCHEME = 'dark'
'''
        
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        # Create a ConfigManager with custom config directory
        manager = ConfigManager()
        original_config_dir = manager.config_dir
        original_config_file = manager.config_file
        
        try:
            # Override config paths for testing
            manager.config_dir = config_dir
            manager.config_file = config_file
            
            # Load the config
            config = manager.load_config()
            
            # Verify backend settings were loaded
            assert hasattr(config, 'PREFERRED_BACKEND'), "Config should have PREFERRED_BACKEND"
            assert config.PREFERRED_BACKEND == 'coregraphics', "Backend should be 'coregraphics'"
            
            assert hasattr(config, 'DESKTOP_FONT_NAME'), "Config should have DESKTOP_FONT_NAME"
            assert config.DESKTOP_FONT_NAME == ['Monaco', 'Menlo'], "Font name should be ['Monaco', 'Menlo']"
            
            assert hasattr(config, 'DESKTOP_FONT_SIZE'), "Config should have DESKTOP_FONT_SIZE"
            assert config.DESKTOP_FONT_SIZE == 16, "Font size should be 16"
            
            assert hasattr(config, 'DESKTOP_WINDOW_WIDTH'), "Config should have DESKTOP_WINDOW_WIDTH"
            assert config.DESKTOP_WINDOW_WIDTH == 1400, "Window width should be 1400"
            
            assert hasattr(config, 'DESKTOP_WINDOW_HEIGHT'), "Config should have DESKTOP_WINDOW_HEIGHT"
            assert config.DESKTOP_WINDOW_HEIGHT == 900, "Window height should be 900"
            
            print("✓ Configuration loading with backend settings test passed")
            
        finally:
            # Restore original paths
            manager.config_dir = original_config_dir
            manager.config_file = original_config_file
            
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_backend_preference_persistence():
    """Test that backend preference can be saved and loaded"""
    # Create a temporary config directory
    temp_dir = tempfile.mkdtemp()
    config_dir = Path(temp_dir) / '.tfm'
    config_file = config_dir / 'config.py'
    
    try:
        # Create config directory
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Write initial config with curses backend
        config_content_curses = '''
class Config:
    PREFERRED_BACKEND = 'curses'
    DESKTOP_FONT_SIZE = 14
'''
        
        with open(config_file, 'w') as f:
            f.write(config_content_curses)
        
        # Load and verify curses backend
        manager = ConfigManager()
        manager.config_dir = config_dir
        manager.config_file = config_file
        
        config = manager.load_config()
        assert config.PREFERRED_BACKEND == 'curses', "Initial backend should be 'curses'"
        
        # Update config to coregraphics backend
        config_content_cg = '''
class Config:
    PREFERRED_BACKEND = 'coregraphics'
    DESKTOP_FONT_SIZE = 16
'''
        
        with open(config_file, 'w') as f:
            f.write(config_content_cg)
        
        # Reload and verify coregraphics backend
        config = manager.reload_config()
        assert config.PREFERRED_BACKEND == 'coregraphics', "Updated backend should be 'coregraphics'"
        assert config.DESKTOP_FONT_SIZE == 16, "Updated font size should be 16"
        
        print("✓ Backend preference persistence test passed")
        
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_all_tests():
    """Run all configuration backend tests"""
    print("\n=== Testing Configuration Backend Settings ===\n")
    
    test_default_backend_config()
    test_backend_validation()
    test_desktop_settings_validation()
    test_config_loading_with_backend()
    test_backend_preference_persistence()
    
    print("\n=== All Configuration Backend Tests Passed ===\n")


if __name__ == '__main__':
    run_all_tests()
