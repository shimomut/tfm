"""
Test script for the sub-shell functionality

Run with: PYTHONPATH=.:src:ttk pytest test/test_subshell.py -v
"""

import os
import sys
from pathlib import Path

def test_subshell_environment():
    """Test that the sub-shell environment variables are set correctly"""
    
    # Check if we're in a TFM sub-shell
    required_vars = ['TFM_LEFT_DIR', 'TFM_RIGHT_DIR', 'TFM_THIS_DIR', 'TFM_OTHER_DIR', 
                     'TFM_LEFT_SELECTED', 'TFM_RIGHT_SELECTED', 'TFM_THIS_SELECTED', 'TFM_OTHER_SELECTED']
    
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
        for var in ['TFM_LEFT_DIR', 'TFM_RIGHT_DIR', 'TFM_THIS_DIR', 'TFM_OTHER_DIR']:
            path = Path(os.environ[var])
            if path.exists() and path.is_dir():
                print(f"✅ {var} is accessible")
            else:
                print(f"❌ {var} is not accessible or doesn't exist")
        
        # Test shell command with environment variables
        print("\nTesting shell command access:")
        try:
            import subprocess
            result = subprocess.run(['bash', '-c', 'echo "Current directory from shell: $TFM_THIS_DIR"'], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                print(f"✅ Shell command output: {result.stdout.strip()}")
            else:
                print("❌ No output from shell command")
        except Exception as e:
            print(f"❌ Error running shell command: {e}")
        
        # Test prompt modification (both PS1 and PROMPT)
        print("\nTesting prompt modification:")
        ps1_value = os.environ.get('PS1', 'Not set')
        prompt_value = os.environ.get('PROMPT', 'Not set')
        
        ps1_has_tfm = '[TFM]' in ps1_value if ps1_value != 'Not set' else False
        prompt_has_tfm = '[TFM]' in prompt_value if prompt_value != 'Not set' else False
        
        if ps1_has_tfm:
            print(f"✅ PS1 contains [TFM] label: {ps1_value}")
        else:
            print(f"ℹ️  PS1: {ps1_value}")
            
        if prompt_has_tfm:
            print(f"✅ PROMPT contains [TFM] label: {prompt_value}")
        else:
            print(f"ℹ️  PROMPT: {prompt_value}")
            
        if ps1_has_tfm or prompt_has_tfm:
            print("✅ Shell prompt modification is working")
        else:
            print("ℹ️  Prompt variables set but may not be active in non-interactive mode")
        
        return True
