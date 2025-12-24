#!/usr/bin/env python3
"""
Direct test for log level filtering functionality.
Tests without using print after LogManager initialization.
"""

import sys
import os
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Save original stdout before importing LogManager
original_stdout = sys.stdout

from tfm_log_manager import LogManager


class MockConfig:
    """Mock configuration object for testing"""
    MAX_LOG_MESSAGES = 100


def main():
    """Run direct test"""
    # Use original stdout for all output
    original_stdout.write("Testing log level filtering...\n")
    original_stdout.flush()
    
    # Create LogManager
    config = MockConfig()
    log_manager = LogManager(config, debug_mode=False)
    
    original_stdout.write("✓ LogManager created\n")
    original_stdout.flush()
    
    # Test 1: Default level
    logger1 = log_manager.getLogger("TestLogger1")
    assert logger1.level == logging.INFO, f"Expected INFO ({logging.INFO}), got {logger1.level}"
    original_stdout.write(f"✓ Test 1: Default level is INFO ({logging.INFO})\n")
    original_stdout.flush()
    
    # Test 2: Set default level
    log_manager.set_default_log_level(logging.DEBUG)
    logger2 = log_manager.getLogger("TestLogger2")
    assert logger2.level == logging.DEBUG, f"Expected DEBUG ({logging.DEBUG}), got {logger2.level}"
    original_stdout.write(f"✓ Test 2: New logger has DEBUG level ({logging.DEBUG})\n")
    original_stdout.flush()
    
    # Test 3: Existing logger updated
    assert logger1.level == logging.DEBUG, f"Expected logger1 updated to DEBUG ({logging.DEBUG}), got {logger1.level}"
    original_stdout.write(f"✓ Test 3: Existing logger updated to DEBUG ({logging.DEBUG})\n")
    original_stdout.flush()
    
    # Test 4: Per-logger override
    log_manager.set_logger_level("SpecialLogger", logging.ERROR)
    logger3 = log_manager.getLogger("SpecialLogger")
    assert logger3.level == logging.ERROR, f"Expected ERROR ({logging.ERROR}), got {logger3.level}"
    original_stdout.write(f"✓ Test 4: Per-logger override to ERROR ({logging.ERROR})\n")
    original_stdout.flush()
    
    # Test 5: Override persists when default changes
    log_manager.set_default_log_level(logging.WARNING)
    assert logger3.level == logging.ERROR, f"Expected logger3 to keep ERROR ({logging.ERROR}), got {logger3.level}"
    original_stdout.write(f"✓ Test 5: Override persists when default changes\n")
    original_stdout.flush()
    
    # Test 6: Non-override logger updated
    assert logger1.level == logging.WARNING, f"Expected logger1 updated to WARNING ({logging.WARNING}), got {logger1.level}"
    original_stdout.write(f"✓ Test 6: Non-override logger updated to WARNING ({logging.WARNING})\n")
    original_stdout.flush()
    
    # Test 7: Get logger level
    level = log_manager.get_logger_level("SpecialLogger")
    assert level == logging.ERROR, f"Expected ERROR ({logging.ERROR}), got {level}"
    original_stdout.write(f"✓ Test 7: get_logger_level returns ERROR ({logging.ERROR})\n")
    original_stdout.flush()
    
    # Test 8: Clear override
    log_manager.clear_logger_level("SpecialLogger")
    assert logger3.level == logging.WARNING, f"Expected logger3 reverted to WARNING ({logging.WARNING}), got {logger3.level}"
    original_stdout.write(f"✓ Test 8: Clear override reverts to default WARNING ({logging.WARNING})\n")
    original_stdout.flush()
    
    # Test 9: Pre-configured level
    log_manager.set_logger_level("FutureLogger", logging.CRITICAL)
    logger4 = log_manager.getLogger("FutureLogger")
    assert logger4.level == logging.CRITICAL, f"Expected CRITICAL ({logging.CRITICAL}), got {logger4.level}"
    original_stdout.write(f"✓ Test 9: Pre-configured level applied ({logging.CRITICAL})\n")
    original_stdout.flush()
    
    # Test 10: isEnabledFor works correctly
    log_manager.set_default_log_level(logging.WARNING)
    logger5 = log_manager.getLogger("FilterTest")
    assert not logger5.isEnabledFor(logging.DEBUG), "DEBUG should be disabled"
    assert not logger5.isEnabledFor(logging.INFO), "INFO should be disabled"
    assert logger5.isEnabledFor(logging.WARNING), "WARNING should be enabled"
    assert logger5.isEnabledFor(logging.ERROR), "ERROR should be enabled"
    original_stdout.write(f"✓ Test 10: isEnabledFor() correctly reflects filtering\n")
    original_stdout.flush()
    
    original_stdout.write("\n✓ ALL TESTS PASSED\n")
    original_stdout.flush()
    
    # Clean up
    log_manager.restore_stdio()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        original_stdout.write(f"✗ ERROR: {e}\n")
        original_stdout.flush()
        import traceback
        traceback.print_exc(file=original_stdout)
        sys.exit(1)
