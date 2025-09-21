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
    """Test that BeyondCompare programs are properly configured"""
    print("Testing BeyondCompare configuration...")
    
    # Get programs from config
    programs = get_programs()
    
    print(f"Found {len(programs)} external programs:")
    for i, prog in enumerate(programs, 1):
        options_str = ""
        if prog.get('options'):
            options_list = [f"{k}={v}" for k, v in prog['options'].items()]
            options_str = f" (options: {', '.join(options_list)})"
        print(f"  {i}. {prog['name']}: {' '.join(prog['command'])}{options_str}")
    
    # Check for both BeyondCompare programs
    programs_to_check = [
        'Compare Directories (BeyondCompare)',
        'Compare Files (BeyondCompare)'
    ]
    
    found_programs = []
    for prog in programs:
        if prog['name'] in programs_to_check:
            found_programs.append(prog['name'])
            options_str = ""
            if prog.get('options'):
                options_list = [f"{k}={v}" for k, v in prog['options'].items()]
                options_str = f" (options: {', '.join(options_list)})"
            print(f"\n✓ {prog['name']} found: {' '.join(prog['command'])}{options_str}")
            
            # Check if the wrapper script exists (adjust path based on current working directory)
            wrapper_path = prog['command'][0]
            if os.path.basename(os.getcwd()) == 'test':
                # When running from test directory, adjust the path
                wrapper_path = '../' + wrapper_path if wrapper_path.startswith('./') else wrapper_path
            
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
    
    # Check if all expected programs were found
    missing_programs = set(programs_to_check) - set(found_programs)
    if missing_programs:
        print(f"✗ Missing BeyondCompare programs: {', '.join(missing_programs)}")
        return False
    
    print("\n✓ BeyondCompare configuration test passed!")
    return True

def test_wrapper_scripts():
    """Test the wrapper scripts with mock environment variables"""
    print("\nTesting wrapper scripts with mock environment...")
    
    # Set mock TFM environment variables for directory comparison
    os.environ['TFM_LEFT_DIR'] = '/tmp/left'
    os.environ['TFM_RIGHT_DIR'] = '/tmp/right'
    
    # Create mock directories and files
    os.makedirs('/tmp/left', exist_ok=True)
    os.makedirs('/tmp/right', exist_ok=True)
    
    # Create test files
    with open('/tmp/left/test.txt', 'w') as f:
        f.write("Left file content")
    with open('/tmp/right/test.txt', 'w') as f:
        f.write("Right file content")
    
    # Set mock file selection environment variables
    os.environ['TFM_LEFT_SELECTED'] = 'test.txt'
    os.environ['TFM_RIGHT_SELECTED'] = 'test.txt'
    
    print("Mock environment set:")
    print(f"  TFM_LEFT_DIR: {os.environ['TFM_LEFT_DIR']}")
    print(f"  TFM_RIGHT_DIR: {os.environ['TFM_RIGHT_DIR']}")
    print(f"  TFM_LEFT_SELECTED: {os.environ['TFM_LEFT_SELECTED']}")
    print(f"  TFM_RIGHT_SELECTED: {os.environ['TFM_RIGHT_SELECTED']}")
    
    success = True
    
    # Test directory comparison wrapper (adjust path based on current working directory)
    wrapper_path = '../tools/bcompare_dirs_wrapper.sh' if os.path.basename(os.getcwd()) == 'test' else './tools/bcompare_dirs_wrapper.sh'
    if os.path.exists(wrapper_path):
        print(f"✓ Directory comparison wrapper ready: {wrapper_path}")
    else:
        print(f"✗ Directory comparison wrapper not found: {wrapper_path}")
        success = False
    
    # Test file comparison wrapper (adjust path based on current working directory)
    files_wrapper_path = '../tools/bcompare_files_wrapper.sh' if os.path.basename(os.getcwd()) == 'test' else './tools/bcompare_files_wrapper.sh'
    if os.path.exists(files_wrapper_path):
        print(f"✓ File comparison wrapper ready: {files_wrapper_path}")
    else:
        print(f"✗ File comparison wrapper not found: {files_wrapper_path}")
        success = False
    
    print("  (Not executing to avoid launching BeyondCompare)")
    return success

if __name__ == '__main__':
    print("BeyondCompare Integration Test")
    print("=" * 40)
    
    success = True
    
    # Test configuration
    if not test_bcompare_config():
        success = False
    
    # Test wrapper scripts
    if not test_wrapper_scripts():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("✓ All tests passed! BeyondCompare is ready to use.")
        print("\nTo use BeyondCompare in TFM:")
        print("1. Start TFM: python3 tfm.py")
        print("2. Press 'x' to open external programs")
        print("3. Select from:")
        print("   - 'Compare Directories (BeyondCompare)' - compares left/right pane directories")
        print("   - 'Compare Files (BeyondCompare)' - compares selected files from both panes")
        print("4. BeyondCompare will open with the appropriate comparison")
    else:
        print("✗ Some tests failed. Please check the configuration.")
    
    sys.exit(0 if success else 1)