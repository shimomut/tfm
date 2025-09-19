#!/usr/bin/env python3
"""
Interactive demo of TFM sub-shell functionality
"""

import os
import subprocess
import sys
from pathlib import Path

def demo_subshell_commands():
    """Demonstrate common sub-shell commands"""
    
    print("TFM Sub-shell Interactive Demo")
    print("=" * 50)
    
    # Set up a demo environment
    env = os.environ.copy()
    current_dir = Path.cwd()
    home_dir = Path.home()
    
    env['TFM_LEFT_DIR'] = str(current_dir)
    env['TFM_RIGHT_DIR'] = str(home_dir)
    env['TFM_THIS_DIR'] = str(current_dir)
    env['TFM_OTHER_DIR'] = str(home_dir)
    # Simulate shell-quoted filenames (including ones with spaces)
    env['TFM_LEFT_SELECTED'] = 'tfm.py README.md \'Creative Cloud Files\''  # Multiple files, one with spaces
    env['TFM_RIGHT_SELECTED'] = 'Documents'        # Cursor position (no explicit selection)
    env['TFM_THIS_SELECTED'] = 'tfm.py README.md'  # Multiple files selected
    env['TFM_OTHER_SELECTED'] = 'Documents'        # Cursor position (no explicit selection)
    env['TFM_ACTIVE'] = '1'
    
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
    
    print("Demo environment setup:")
    print(f"  Active pane (TFM_THIS_DIR): {env['TFM_THIS_DIR']}")
    print(f"  Other pane (TFM_OTHER_DIR): {env['TFM_OTHER_DIR']}")
    print(f"  Selected files: {env['TFM_THIS_SELECTED']}")
    print()
    
    commands = [
        {
            'description': 'List files in both panes',
            'command': 'echo "Left pane:" && ls -la "$TFM_LEFT_DIR" | head -5 && echo "Right pane:" && ls -la "$TFM_RIGHT_DIR" | head -5'
        },
        {
            'description': 'List selected files directly (works with spaces!)',
            'command': 'cd "$TFM_THIS_DIR" && echo "Selected files:" && ls -la $TFM_THIS_SELECTED 2>/dev/null || echo "Could not list files"'
        },
        {
            'description': 'Show how filenames are automatically quoted',
            'command': 'echo "Left pane files (note quoting): $TFM_LEFT_SELECTED" && echo "This includes files with spaces properly quoted!"'
        },
        {
            'description': 'Compare directory sizes',
            'command': 'echo "Directory sizes:" && du -sh "$TFM_LEFT_DIR" "$TFM_RIGHT_DIR" 2>/dev/null || echo "Could not get directory sizes"'
        },
        {
            'description': 'Find Python files in both directories',
            'command': 'echo "Python files:" && find "$TFM_LEFT_DIR" "$TFM_RIGHT_DIR" -name "*.py" -type f 2>/dev/null | head -5'
        },
        {
            'description': 'Show environment variables',
            'command': 'echo "TFM Environment Variables:" && env | grep "^TFM_" | sort'
        },
        {
            'description': 'Demonstrate selection behavior',
            'command': 'echo "Left pane (multiple selected): $TFM_LEFT_SELECTED" && echo "Right pane (cursor position): $TFM_RIGHT_SELECTED" && echo "This shows both explicit selection and cursor fallback"'
        },
        {
            'description': 'Show shell prompts with TFM label',
            'command': 'echo "Bash prompt (PS1): $PS1" && echo "Zsh prompt (PROMPT): $PROMPT"'
        }
    ]
    
    for i, cmd_info in enumerate(commands, 1):
        print(f"{i}. {cmd_info['description']}")
        print(f"   Command: {cmd_info['command']}")
        print("   Output:")
        
        try:
            result = subprocess.run(['bash', '-c', cmd_info['command']], 
                                  env=env, 
                                  capture_output=True, 
                                  text=True,
                                  cwd=current_dir)
            
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    print(f"     {line}")
            
            if result.stderr:
                print(f"     Error: {result.stderr.strip()}")
                
        except Exception as e:
            print(f"     Error running command: {e}")
        
        print()
    
    print("=" * 50)
    print("This demonstrates how TFM sub-shell environment variables")
    print("can be used in shell commands for advanced file operations.")
    print()
    print("To use in TFM:")
    print("1. Start TFM: python3 tfm.py")
    print("2. Navigate and select files")
    print("3. Press 'x' to enter sub-shell mode")
    print("4. Use the environment variables in your commands")
    print("5. Type 'exit' to return to TFM")

if __name__ == "__main__":
    demo_subshell_commands()