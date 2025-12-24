#!/usr/bin/env python3
"""
Test configuration management for LogManager
"""

import sys
import os
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_log_manager import LogManager, LoggingConfig


class MockConfig:
    """Mock configuration object"""
    MAX_LOG_MESSAGES = 100


def test_logging_config_defaults():
    """Test LoggingConfig dataclass has correct defaults"""
    config = LoggingConfig()
    
    # Log pane settings
    assert config.log_pane_enabled == True
    assert config.max_log_messages == 1000
    
    # Stream output settings
    assert config.stream_output_enabled is None
    assert config.stream_output_desktop_default == True
    assert config.stream_output_terminal_default == False
    
    # Remote monitoring settings
    assert config.remote_monitoring_enabled == False
    assert config.remote_monitoring_port is None
    
    # Log level settings
    assert config.default_log_level == logging.INFO
    assert config.logger_levels == {}
    
    # Format settings
    assert config.timestamp_format == "%H:%M:%S"
    assert config.message_format == "%(asctime)s [%(name)s] %(message)s"
    
    print("✓ LoggingConfig defaults are correct")


def test_logging_config_custom_values():
    """Test LoggingConfig can be created with custom values"""
    config = LoggingConfig(
        log_pane_enabled=False,
        max_log_messages=500,
        stream_output_enabled=True,
        remote_monitoring_enabled=True,
        remote_monitoring_port=9999,
        default_log_level=logging.DEBUG,
        logger_levels={"Main": logging.WARNING}
    )
    
    assert config.log_pane_enabled == False
    assert config.max_log_messages == 500
    assert config.stream_output_enabled == True
    assert config.remote_monitoring_enabled == True
    assert config.remote_monitoring_port == 9999
    assert config.default_log_level == logging.DEBUG
    assert config.logger_levels == {"Main": logging.WARNING}
    
    print("✓ LoggingConfig accepts custom values")


def test_configure_handlers_method_exists():
    """Test that configure_handlers method exists and is callable"""
    mock_config = MockConfig()
    log_manager = LogManager(mock_config, debug_mode=False)
    
    # Check method exists
    assert hasattr(log_manager, 'configure_handlers')
    assert callable(log_manager.configure_handlers)
    
    # Check it can be called with no arguments
    log_manager.configure_handlers()
    
    # Check it can be called with arguments
    log_manager.configure_handlers(
        log_pane_enabled=True,
        stream_output_enabled=False,
        remote_enabled=False
    )
    
    # Cleanup
    log_manager.restore_stdio()
    
    print("✓ configure_handlers method exists and is callable")


def test_log_manager_has_config():
    """Test that LogManager stores configuration"""
    mock_config = MockConfig()
    log_manager = LogManager(mock_config, debug_mode=False)
    
    # Check that LogManager has _config attribute
    assert hasattr(log_manager, '_config')
    assert isinstance(log_manager._config, LoggingConfig)
    
    # Check that configuration was initialized
    assert log_manager._config.max_log_messages == 100  # From MockConfig
    
    # Cleanup
    log_manager.restore_stdio()
    
    print("✓ LogManager stores configuration")


def test_handler_attributes_exist():
    """Test that LogManager has handler attributes"""
    mock_config = MockConfig()
    log_manager = LogManager(mock_config, debug_mode=False)
    
    # Check handler attributes exist
    assert hasattr(log_manager, '_log_pane_handler')
    assert hasattr(log_manager, '_stream_output_handler')
    assert hasattr(log_manager, '_remote_monitoring_handler')
    
    # Initially, handlers should be None (not configured yet)
    assert log_manager._log_pane_handler is None
    assert log_manager._stream_output_handler is None
    assert log_manager._remote_monitoring_handler is None
    
    # Cleanup
    log_manager.restore_stdio()
    
    print("✓ LogManager has handler attributes")


if __name__ == '__main__':
    print("Testing configuration management...")
    print()
    
    test_logging_config_defaults()
    test_logging_config_custom_values()
    test_configure_handlers_method_exists()
    test_log_manager_has_config()
    test_handler_attributes_exist()
    
    print()
    print("All configuration management tests passed!")
