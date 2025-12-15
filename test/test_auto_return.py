#!/usr/bin/env python3
"""
Test script to verify the auto_return option functionality
"""

import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_config import get_programs

def test_options_parsing():
    """Test that program options are properly parsed"""
    print("Testing program options parsing...")
    
    programs = get_programs()
    
    # Find BeyondCompare programs and check their options
    bcompare_programs = [p for p in programs if 'BeyondCompare' in p['name']]
    
    if not bcompare_programs:
        print("✗ No BeyondCompare programs found")
        return False
    
    success = True
    for prog in bcompare_programs:
        print(f"\nProgram: {prog['name']}")
        print(f"Command: {' '.join(prog['command'])}")
        
        if 'options' in prog:
            print(f"Options: {prog['options']}")
            
            # Check if auto_return is set
            if prog['options'].get('auto_return'):
                print("✓ auto_return option is enabled")
            else:
                print("✗ auto_return option is not enabled")
                success = False
        else:
            print("✗ No options found")
            success = False
    
    return success

def create_test_program():
    """Create a simple test program to demonstrate auto_return"""
    test_script = """#!/bin/bash
echo "Test program running..."
echo "This program will auto-return to TFM"
sleep 2
echo "Test program completed"
"""
    
    with open('test_program.sh', 'w') as f:
        f.write(test_script)
    
    os.chmod('test_program.sh', 0o755)
    print("✓ Created test_program.sh")
    
    # Add to user config temporarily for testing
    config_addition = """
        {'name': 'Test Auto Return', 'command': ['./test_program.sh'], 'options': {'auto_return': True}},"""
    
    print("To test auto_return functionality:")
    print("1. Add this to your ~/.tfm/config.py PROGRAMS list:")
    print(config_addition)
    print("2. Start TFM and press 'x'")
    print("3. Select 'Test Auto Return'")
    print("4. The program should run and automatically return to TFM")

if __name__ == '__main__':
    print("Auto Return Option Test")
    print("=" * 30)
    
    success = test_options_parsing()
    
    if success:
        print("\n✓ Options parsing test passed!")
        create_test_program()
    else:
        print("\n✗ Options parsing test failed!")
    
    print("\nProgram options format:")
    print("{'name': 'Program Name', 'command': ['command'], 'options': {'auto_return': True}}")
    
    sys.exit(0 if success else 1)