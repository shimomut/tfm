#!/usr/bin/env python3
"""Simple integration test to verify basic functionality."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

print("Starting simple integration test...")

try:
    from tfm_log_manager import LogManager, LoggingConfig
    print("✓ Imported LogManager and LoggingConfig")
except Exception as e:
    print(f"✗ Failed to import: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    config = LoggingConfig(
        log_pane_enabled=True,
        stream_output_enabled=False,
        remote_monitoring_enabled=False
    )
    print("✓ Created LoggingConfig")
except Exception as e:
    print(f"✗ Failed to create config: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    log_manager = LogManager(config)
    print("✓ Created LogManager")
except Exception as e:
    print(f"✗ Failed to create LogManager: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    logger = log_manager.getLogger("Test")
    print("✓ Got logger")
except Exception as e:
    print(f"✗ Failed to get logger: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    logger.info("Test message")
    print("✓ Logged message")
except Exception as e:
    print(f"✗ Failed to log message: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    messages = log_manager.log_pane_handler.get_messages()
    print(f"✓ Got {len(messages)} messages")
    for msg in messages:
        print(f"  {msg}")
except Exception as e:
    print(f"✗ Failed to get messages: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✓ Simple integration test passed!")
