#!/usr/bin/env python3
"""
Simple checkpoint test to isolate the issue.
"""

import sys
sys.path.insert(0, 'src')

print("Step 1: Importing modules...")
try:
    from tfm_log_manager import LogManager
    print("✓ Imported LogManager")
except Exception as e:
    print(f"✗ Failed to import LogManager: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nStep 2: Creating minimal config...")
class MinimalConfig:
    MAX_LOG_MESSAGES = 1000

config = MinimalConfig()
print("✓ Created config")

print("\nStep 3: Creating LogManager...")
try:
    log_manager = LogManager(config, remote_port=None, debug_mode=False)
    print("✓ Created LogManager")
except Exception as e:
    print(f"✗ Failed to create LogManager: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nStep 4: Configuring handlers...")
try:
    log_manager.configure_handlers(
        log_pane_enabled=True,
        stream_output_enabled=False,
        remote_enabled=False
    )
    print("✓ Configured handlers")
except Exception as e:
    print(f"✗ Failed to configure handlers: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nStep 5: Getting logger...")
try:
    logger = log_manager.getLogger("TestLogger")
    print(f"✓ Got logger: {logger}")
    print(f"  Logger type: {type(logger)}")
    print(f"  Logger name: {logger.name}")
    print(f"  Logger handlers: {logger.handlers}")
except Exception as e:
    print(f"✗ Failed to get logger: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nStep 6: Emitting test message...")
try:
    logger.info("Test message")
    print("✓ Emitted test message")
except Exception as e:
    print(f"✗ Failed to emit message: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✓ ALL STEPS COMPLETED SUCCESSFULLY")
