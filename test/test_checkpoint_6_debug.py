#!/usr/bin/env python3
"""
Debug test to find the hanging issue.
"""

import sys
sys.path.insert(0, 'src')

print("Step 1: Testing basic logging without custom handler...")
import logging

logger = logging.getLogger("TestLogger")
logger.setLevel(logging.INFO)

# Add a simple stream handler
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

print("Step 2: Emitting message with standard handler...")
logger.info("Test message")
print("✓ Standard logging works")

print("\nStep 3: Testing custom handler...")
from tfm_logging_handlers import LogPaneHandler

custom_handler = LogPaneHandler(max_messages=100)
print(f"✓ Created custom handler: {custom_handler}")

logger2 = logging.getLogger("TestLogger2")
logger2.setLevel(logging.INFO)
logger2.propagate = False
logger2.addHandler(custom_handler)

print("Step 4: About to emit message with custom handler...")
sys.stdout.flush()

# Try to emit
try:
    print("  Calling logger2.info()...")
    sys.stdout.flush()
    logger2.info("Test message")
    print("✓ Custom handler works")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n✓ DONE")
