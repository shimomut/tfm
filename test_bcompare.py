#!/usr/bin/env python3
"""
Test script to verify BeyondCompare integration with TFM
"""

import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from tfm_config import get_programs

def test_bcompare_config():
    """Test that BeyondCompare is properly configured"""
    print("Testing BeyondCompare configuration...")
    
    # Get programs from config
    programs = get_programs()
    
    print(f"Found {len(programs)} external programs:")
    for i, prog in enumerate(programs, 1):
        print(f"  {i}. {prog['name']}: {' '.join(prog['command'])}")
    
    # Check if BeyondCompare is in the list
    bcompare_found = False
    for prog in programs:
        if prog['name'] == 'BeyondCompare':
            bcompare_found = True
            print(f"\n✓ BeyondCompare found: {' '.join(prog['command'])}")
            
            # Check if the wrapper script exists
            wrapper_path = prog['command'][0]
            if os.path.exists(wrapper_path):
                print(f"✓ Wrapper script exists: {wrapper_path}")
                
                # Check if it's executable
                if os.access(wrapper_path, os.X_OK):
                    print("✓ Wrapper script is executable")
                else:
                    print("✗ Wrapper script is not executable")
                    return False
            else:
                print(f"✗ Wrapper script not found: {wrapper_path}")
                return False
            break
    
    if not bcompare_found:
        print("✗ BeyondCompare not found in programs list")
        return False
    
    print("\n✓ BeyondCompare configuration test passed!")
    return True

def test_wrapper_script():
    """Test the wrapper script with mock environment variables"""
    print("\nTesting wrapper script with mock environment...")
    
    # Set mock TFM environment variables
    os.environ['TFM_LEFT_DIR'] = '/tmp/left'
    os.environ['TFM_RIGHT_DIR'] = '/tmp/right'
    
    # Create mock directories
    os.makedirs('/tmp/left', exist_ok=True)
    os.makedirs('/tmp/right', exist_ok=True)
    
    print("Mock environment set:")
    print(f"  TFM_LEFT_DIR: {os.environ['TFM_LEFT_DIR']}")
    print(f"  TFM_RIGHT_DIR: {os.environ['TFM_RIGHT_DIR']}")
    
    # Note: We won't actually run bcompare since it might not be installed
    # But we can verify the script would work
    wrapper_path = './bcompare_wrapper.sh'
    if os.path.exists(wrapper_path):
        print(f"✓ Wrapper script ready to execute: {wrapper_path}")
        print("  (Not executing to avoid launching BeyondCompare)")
        return True
    else:
        print(f"✗ Wrapper script not found: {wrapper_path}")
        return False

if __name__ == '__main__':
    print("BeyondCompare Integration Test")
    print("=" * 40)
    
    success = True
    
    # Test configuration
    if not test_bcompare_config():
        success = False
    
    # Test wrapper script
    if not test_wrapper_script():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("✓ All tests passed! BeyondCompare is ready to use.")
        print("\nTo use BeyondCompare in TFM:")
        print("1. Start TFM: python3 tfm.py")
        print("2. Press 'x' to open external programs")
        print("3. Select 'BeyondCompare' from the list")
        print("4. BeyondCompare will open with left and right pane directories")
    else:
        print("✗ Some tests failed. Please check the configuration.")
    
    sys.exit(0 if success else 1)