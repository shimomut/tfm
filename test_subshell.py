#!/usr/bin/env python3
"""
Test script for the sub-shell functionality
"""

import os
import sys
from pathlib import Path

def test_subshell_environment():
    """Test that the sub-shell environment variables are set correctly"""
    
    # Check if we're in a TFM sub-shell
    required_vars = ['LEFT_DIR', 'RIGHT_DIR', 'THIS_DIR', 'OTHER_DIR', 
                     'LEFT_SELECTED', 'RIGHT_SELECTED', 'THIS_SELECTED', 'OTHER_SELECTED']
    
    print("TFM Sub-shell Environment Test")
    print("=" * 40)
    
    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var)
        if value is not None:
            print(f"{var}: '{value}'")
        else:
            missing_vars.append(var)
            print(f"{var}: NOT SET")
    
    print("=" * 40)
    
    if missing_vars:
        print(f"❌ Missing variables: {', '.join(missing_vars)}")
        print("This script should be run from within TFM sub-shell mode (press 'x' in TFM)")
        return False
    else:
        print("✅ All TFM environment variables are set correctly!")
        
        # Test directory access
        print("\nTesting directory access:")
        for var in ['LEFT_DIR', 'RIGHT_DIR', 'THIS_DIR', 'OTHER_DIR']:
            path = Path(os.environ[var])
            if path.exists() and path.is_dir():
                print(f"✅ {var} is accessible")
            else:
                print(f"❌ {var} is not accessible or doesn't exist")
        
        # Test shell command with environment variables
        print("\nTesting shell command access:")
        try:
            import subprocess
            result = subprocess.run(['bash', '-c', 'echo "Current directory from shell: $THIS_DIR"'], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                print(f"✅ Shell command output: {result.stdout.strip()}")
            else:
                print("❌ No output from shell command")
        except Exception as e:
            print(f"❌ Error running shell command: {e}")
        
        return True

if __name__ == "__main__":
    test_subshell_environment()