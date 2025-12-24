#!/usr/bin/env python3
"""
Simple test for Task 15: Update existing code to use new logging
"""

import sys
import os
import traceback
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    print("Importing modules...")
    from tfm_log_manager import LogManager
    from tfm_config import get_config
    print("✓ Imports successful")
    
    print("\nCreating LogManager...")
    config = get_config()
    log_manager = LogManager(config)
    print("✓ LogManager created")
    
    print("\nCreating Main logger...")
    main_logger = log_manager.getLogger("Main")
    print(f"✓ Main logger created: {main_logger.name}")
    
    print("\nTesting logger methods...")
    main_logger.info("Test info message")
    main_logger.warning("Test warning message")
    main_logger.error("Test error message")
    print("✓ Logger methods work")
    
    print("\nChecking log messages...")
    messages = log_manager.get_log_messages()
    print(f"✓ {len(messages)} messages logged")
    
    print("\n" + "=" * 50)
    print("All tests passed! ✓")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    traceback.print_exc()
    sys.exit(1)
