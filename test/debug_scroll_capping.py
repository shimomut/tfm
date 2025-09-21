#!/usr/bin/env python3
"""
Debug script for log scroll capping
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

print("Starting debug test...")

from tfm_log_manager import LogManager
from tfm_config import get_config

print("Imported modules")

config = get_config()
log_manager = LogManager(config)

# Use original stdout for output since LogManager redirects stdout
original_stdout = log_manager.original_stdout

original_stdout.write("Created log manager\n")

# Add test messages
log_manager.log_messages.clear()
for i in range(10):
    log_manager.log_messages.append((f'2024-01-01 12:00:{i:02d}', 'TEST', f'Message {i}'))

original_stdout.write(f"Added {len(log_manager.log_messages)} messages\n")
original_stdout.write(f"Initial offset: {log_manager.log_scroll_offset}\n")

# Test the capping logic directly
total_messages = len(log_manager.log_messages)
display_height = 5
max_scroll = max(0, total_messages - display_height)
original_stdout.write(f"Calculated max_scroll: {max_scroll}\n")

# Set offset beyond limit
log_manager.log_scroll_offset = 1000
original_stdout.write(f"Set offset to: {log_manager.log_scroll_offset}\n")

# Apply capping
log_manager.log_scroll_offset = min(log_manager.log_scroll_offset, max_scroll)
original_stdout.write(f"After capping: {log_manager.log_scroll_offset}\n")
original_stdout.write(f"Capping works: {log_manager.log_scroll_offset == max_scroll}\n")

original_stdout.write("Debug test completed\n")