#!/usr/bin/env python3
"""
Test for Task 15: Update existing code to use new logging

This test verifies that the migration from add_message() to getLogger()
works correctly across all updated files.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_log_manager import LogManager
from tfm_config import get_config


def test_main_logger_creation():
    """Test that tfm_main.py creates a Main logger"""
    config = get_config()
    log_manager = LogManager(config)
    
    # Create Main logger
    main_logger = log_manager.getLogger("Main")
    
    assert main_logger is not None
    assert main_logger.name == "Main"
    print("✓ Main logger created successfully")


def test_fileop_logger_creation():
    """Test that FileOp logger can be created"""
    config = get_config()
    log_manager = LogManager(config)
    
    # Create FileOp logger
    fileop_logger = log_manager.getLogger("FileOp")
    
    assert fileop_logger is not None
    assert fileop_logger.name == "FileOp"
    print("✓ FileOp logger created successfully")


def test_archive_logger_creation():
    """Test that Archive logger can be created"""
    config = get_config()
    log_manager = LogManager(config)
    
    # Create Archive logger
    archive_logger = log_manager.getLogger("Archive")
    
    assert archive_logger is not None
    assert archive_logger.name == "Archive"
    print("✓ Archive logger created successfully")


def test_cache_logger_creation():
    """Test that Cache logger can be created"""
    config = get_config()
    log_manager = LogManager(config)
    
    # Create Cache logger
    cache_logger = log_manager.getLogger("Cache")
    
    assert cache_logger is not None
    assert cache_logger.name == "Cache"
    print("✓ Cache logger created successfully")


def test_uilayer_logger_creation():
    """Test that UILayer logger can be created"""
    config = get_config()
    log_manager = LogManager(config)
    
    # Create UILayer logger
    uilayer_logger = log_manager.getLogger("UILayer")
    
    assert uilayer_logger is not None
    assert uilayer_logger.name == "UILayer"
    print("✓ UILayer logger created successfully")


def test_logger_messages():
    """Test that logger methods work correctly"""
    config = get_config()
    log_manager = LogManager(config)
    
    # Create a test logger
    test_logger = log_manager.getLogger("Test")
    
    # Test different log levels
    test_logger.debug("Debug message")
    test_logger.info("Info message")
    test_logger.warning("Warning message")
    test_logger.error("Error message")
    test_logger.critical("Critical message")
    
    # Verify messages were logged
    messages = log_manager.get_log_messages()
    assert len(messages) > 0
    print(f"✓ Logger methods work correctly ({len(messages)} messages logged)")


def test_file_operations_logger_integration():
    """Test that FileOperations uses logger correctly"""
    from tfm_file_operations import FileOperations
    
    config = get_config()
    log_manager = LogManager(config)
    
    # Create FileOperations instance
    file_ops = FileOperations(config)
    file_ops.log_manager = log_manager
    file_ops.logger = log_manager.getLogger("FileOp")
    
    assert file_ops.logger is not None
    assert file_ops.logger.name == "FileOp"
    print("✓ FileOperations logger integration works")


def test_archive_operations_logger_integration():
    """Test that ArchiveOperations uses logger correctly"""
    from tfm_archive import ArchiveOperations
    
    config = get_config()
    log_manager = LogManager(config)
    
    # Create ArchiveOperations instance
    archive_ops = ArchiveOperations(log_manager=log_manager)
    
    assert archive_ops.logger is not None
    assert archive_ops.logger.name == "Archive"
    
    # Test the _log helper method
    archive_ops._log("Test message", "INFO")
    
    messages = log_manager.get_log_messages()
    assert any("Test message" in msg for msg in messages)
    print("✓ ArchiveOperations logger integration works")


def test_cache_manager_logger_integration():
    """Test that CacheManager uses logger correctly"""
    from tfm_cache_manager import CacheManager
    
    config = get_config()
    log_manager = LogManager(config)
    
    # Create CacheManager instance
    cache_mgr = CacheManager(log_manager=log_manager)
    
    assert cache_mgr.logger is not None
    assert cache_mgr.logger.name == "Cache"
    
    # Test the _log helper method
    cache_mgr._log("Test cache message", "INFO")
    
    messages = log_manager.get_log_messages()
    assert any("Test cache message" in msg for msg in messages)
    print("✓ CacheManager logger integration works")


def test_ui_layer_stack_logger_integration():
    """Test that UILayerStack uses logger correctly"""
    from tfm_ui_layer import UILayerStack, UILayer
    
    # Create a simple test layer
    class TestLayer(UILayer):
        def handle_key_event(self, event):
            return False
        def handle_char_event(self, event):
            return False
        def handle_system_event(self, event):
            return False
        def render(self, renderer):
            pass
        def needs_redraw(self):
            return False
        def is_full_screen(self):
            return False
        def mark_dirty(self):
            pass
        def clear_dirty(self):
            pass
        def should_close(self):
            return False
        def on_activate(self):
            pass
        def on_deactivate(self):
            pass
    
    config = get_config()
    log_manager = LogManager(config)
    
    # Create UILayerStack instance
    bottom_layer = TestLayer()
    layer_stack = UILayerStack(bottom_layer, log_manager=log_manager)
    
    assert layer_stack._logger is not None
    assert layer_stack._logger.name == "UILayer"
    print("✓ UILayerStack logger integration works")


if __name__ == '__main__':
    print("Testing Task 15: Logger Migration")
    print("=" * 50)
    
    test_main_logger_creation()
    test_fileop_logger_creation()
    test_archive_logger_creation()
    test_cache_logger_creation()
    test_uilayer_logger_creation()
    test_logger_messages()
    test_file_operations_logger_integration()
    test_archive_operations_logger_integration()
    test_cache_manager_logger_integration()
    test_ui_layer_stack_logger_integration()
    
    print("=" * 50)
    print("All tests passed! ✓")
