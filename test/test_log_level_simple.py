#!/usr/bin/env python3
"""
Simple test for log level filtering functionality.
"""

import sys
import os
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_log_manager import LogManager


class MockConfig:
    """Mock configuration object for testing"""
    MAX_LOG_MESSAGES = 100


def main():
    """Run simple test"""
    print("Testing log level filtering...")
    
    # Create LogManager
    config = MockConfig()
    log_manager = LogManager(config, debug_mode=False)
    
    print("✓ LogManager created")
    
    # Test 1: Default level
    logger1 = log_manager.getLogger("TestLogger1")
    print(f"✓ Logger1 level: {logger1.level} (expected {logging.INFO})")
    assert logger1.level == logging.INFO
    
    # Test 2: Set default level
    log_manager.set_default_log_level(logging.DEBUG)
    logger2 = log_manager.getLogger("TestLogger2")
    print(f"✓ Logger2 level: {logger2.level} (expected {logging.DEBUG})")
    assert logger2.level == logging.DEBUG
    
    # Test 3: Per-logger override
    log_manager.set_logger_level("SpecialLogger", logging.ERROR)
    logger3 = log_manager.getLogger("SpecialLogger")
    print(f"✓ Logger3 level: {logger3.level} (expected {logging.ERROR})")
    assert logger3.level == logging.ERROR
    
    # Test 4: Get logger level
    level = log_manager.get_logger_level("SpecialLogger")
    print(f"✓ Get logger level: {level} (expected {logging.ERROR})")
    assert level == logging.ERROR
    
    print("\n✓ ALL TESTS PASSED")
    
    # Clean up
    log_manager.restore_stdio()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
