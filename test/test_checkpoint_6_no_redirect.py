#!/usr/bin/env python3
"""
Test without stdout/stderr redirection to isolate the issue.
"""

import sys
import logging

# Save original streams before any imports
original_stdout = sys.stdout
original_stderr = sys.stderr

sys.path.insert(0, 'src')

# Import after saving streams
from tfm_logging_handlers import LogPaneHandler

print("Step 1: Testing LogPaneHandler directly...")

# Create handler
handler = LogPaneHandler(max_messages=100)
print(f"✓ Created LogPaneHandler: {handler}")

# Create a test logger
logger = logging.getLogger("TestLogger")
logger.setLevel(logging.INFO)
logger.propagate = False
logger.addHandler(handler)

print(f"✓ Created logger with handler")

# Emit a message
print("Step 2: Emitting test message...")
sys.stdout.flush()
sys.__stdout__.write("[BEFORE] About to call logger.info()\n")
sys.__stdout__.flush()
logger.info("Test message from logger")
sys.__stdout__.write("[AFTER] Called logger.info()\n")
sys.__stdout__.flush()
print("✓ Message emitted")

# Check messages
print("Step 3: Checking messages...")
messages = list(handler.messages)
print(f"✓ Got {len(messages)} messages")
if messages:
    print(f"  Last message: {messages[-1]}")

# Test stream capture simulation
print("\nStep 4: Testing stream capture simulation...")
record = logging.LogRecord(
    name="STDOUT",
    level=logging.INFO,
    pathname="",
    lineno=0,
    msg="Raw stdout text",
    args=(),
    exc_info=None
)
record.is_stream_capture = True

handler.emit(record)
print("✓ Emitted stream capture record")

messages = list(handler.messages)
print(f"✓ Got {len(messages)} messages")
if messages:
    print(f"  Last message: {messages[-1]}")

print("\n✓ ALL TESTS PASSED")
