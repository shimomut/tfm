#!/usr/bin/env python3
"""
Test TFM sub-shell functionality by simulating the environment setup
"""

import os
import subprocess
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

def simulate_tfm_subshell():
    """Simulate what TFM does when entering sub-shell mode"""
    
    print("Simulating TFM sub-shell environment setup...")
    print("=" * 50)
    
    # Simulate TFM's environment setup
    env = os.environ.copy()
    
    # Set up directory variables (using current directory structure)
    current_dir = Path.cwd()
    home_dir = Path.home()
    
    env['TFM_LEFT_DIR'] = str(current_dir)
    env['TFM_RIGHT_DIR'] = str(home_dir)
    env['TFM_THIS_DIR'] = str(current_dir)
    env['TFM_OTHER_DIR'] = str(home_dir)
    
    # Set up selected files (simulate some selections)
    env['TFM_LEFT_SELECTED'] = 'tfm.py README.md'
    env['TFM_RIGHT_SELECTED'] = ''
    env['TFM_THIS_SELECTED'] = 'tfm.py README.md'
    env['TFM_OTHER_SELECTED'] = ''
    
    # Add prompt modification like TFM does (both PS1 and PROMPT)
    current_ps1 = env.get('PS1', '')
    current_prompt = env.get('PROMPT', '')
    
    if current_ps1:
        env['PS1'] = f'[TFM] {current_ps1}'
    else:
        env['PS1'] = '[TFM] \\u@\\h:\\w\\$ '
    
    if current_prompt:
        env['PROMPT'] = f'[TFM] {current_prompt}'
    else:
        env['PROMPT'] = '[TFM] %n@%m:%~%# '
    
    print("Environment variables set:")
    for var in ['TFM_LEFT_DIR', 'TFM_RIGHT_DIR', 'TFM_THIS_DIR', 'TFM_OTHER_DIR', 
                'TFM_LEFT_SELECTED', 'TFM_RIGHT_SELECTED', 'TFM_THIS_SELECTED', 'TFM_OTHER_SELECTED']:
        print(f"  {var}: {env[var]}")
    
    print("\n" + "=" * 50)
    print("Testing sub-shell with environment variables...")
    
    # Test running our verification script
    try:
        result = subprocess.run(['bash', 'verify_subshell.sh'], 
                              env=env, 
                              capture_output=True, 
                              text=True,
                              cwd=current_dir)
        
        print("Verification script output:")
        print(result.stdout)
        
        if result.stderr:
            print("Errors:")
            print(result.stderr)
            
        if result.returncode == 0:
            print("✅ Sub-shell environment test PASSED!")
            return True
        else:
            print("❌ Sub-shell environment test FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def test_python_script():
    """Test the Python verification script"""
    
    print("\nTesting Python verification script...")
    print("=" * 50)
    
    # Set up environment
    env = os.environ.copy()
    current_dir = Path.cwd()
    home_dir = Path.home()
    
    env['TFM_LEFT_DIR'] = str(current_dir)
    env['TFM_RIGHT_DIR'] = str(home_dir)
    env['TFM_THIS_DIR'] = str(current_dir)
    env['TFM_OTHER_DIR'] = str(home_dir)
    env['TFM_LEFT_SELECTED'] = 'test1.txt test2.txt'
    env['TFM_RIGHT_SELECTED'] = ''
    env['TFM_THIS_SELECTED'] = 'test1.txt test2.txt'
    env['TFM_OTHER_SELECTED'] = ''
    
    # Add prompt modification like TFM does (both PS1 and PROMPT)
    current_ps1 = env.get('PS1', '')
    current_prompt = env.get('PROMPT', '')
    
    if current_ps1:
        env['PS1'] = f'[TFM] {current_ps1}'
    else:
        env['PS1'] = '[TFM] \\u@\\h:\\w\\$ '
    
    if current_prompt:
        env['PROMPT'] = f'[TFM] {current_prompt}'
    else:
        env['PROMPT'] = '[TFM] %n@%m:%~%# '
    
    try:
        result = subprocess.run([sys.executable, 'test_subshell.py'], 
                              env=env, 
                              capture_output=True, 
                              text=True,
                              cwd=current_dir)
        
        print("Python test output:")
        print(result.stdout)
        
        if result.stderr:
            print("Errors:")
            print(result.stderr)
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running Python test: {e}")
        return False

if __name__ == "__main__":
    print("TFM Sub-shell Functionality Test")
    print("=" * 60)
    
    # Test 1: Shell script verification
    test1_passed = simulate_tfm_subshell()
    
    # Test 2: Python script verification  
    test2_passed = test_python_script()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"  Shell verification: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"  Python verification: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests PASSED! Sub-shell functionality is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests FAILED. Check the implementation.")
        sys.exit(1)