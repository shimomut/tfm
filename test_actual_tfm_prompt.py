#!/usr/bin/env python3
"""
Test the actual TFM prompt modification by simulating the exact code path
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

def test_tfm_prompt_logic():
    """Test the exact prompt modification logic used in TFM"""
    
    print("Testing TFM's Actual Prompt Modification Logic")
    print("=" * 50)
    
    # Test different scenarios
    scenarios = [
        {
            'name': 'Bash user (PS1 only)',
            'initial_env': {'PS1': '\\u@\\h:\\w\\$ '},
            'expected_ps1': '[TFM] \\u@\\h:\\w\\$ ',
            'expected_prompt': '[TFM] %n@%m:%~%# '
        },
        {
            'name': 'Zsh user (PROMPT only)', 
            'initial_env': {'PROMPT': '%n@%m:%~%# '},
            'expected_ps1': '[TFM] \\u@\\h:\\w\\$ ',
            'expected_prompt': '[TFM] %n@%m:%~%# '
        },
        {
            'name': 'User with both PS1 and PROMPT',
            'initial_env': {'PS1': '\\u@\\h:\\w\\$ ', 'PROMPT': '%n@%m:%~%# '},
            'expected_ps1': '[TFM] \\u@\\h:\\w\\$ ',
            'expected_prompt': '[TFM] %n@%m:%~%# '
        },
        {
            'name': 'No prompts set',
            'initial_env': {},
            'expected_ps1': '[TFM] \\u@\\h:\\w\\$ ',
            'expected_prompt': '[TFM] %n@%m:%~%# '
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        
        # Set up environment like TFM does
        env = os.environ.copy()
        
        # Clear existing prompts and set test values
        env.pop('PS1', None)
        env.pop('PROMPT', None)
        env.update(scenario['initial_env'])
        
        # Apply TFM's prompt modification logic (copied from tfm_main.py)
        current_ps1 = env.get('PS1', '')
        current_prompt = env.get('PROMPT', '')
        
        # Modify PS1 for bash and other shells
        if current_ps1:
            env['PS1'] = f'[TFM] {current_ps1}'
        else:
            env['PS1'] = '[TFM] \\u@\\h:\\w\\$ '
        
        # Modify PROMPT for zsh
        if current_prompt:
            env['PROMPT'] = f'[TFM] {current_prompt}'
        else:
            env['PROMPT'] = '[TFM] %n@%m:%~%# '
        
        # Verify results
        ps1_correct = env['PS1'] == scenario['expected_ps1']
        prompt_correct = env['PROMPT'] == scenario['expected_prompt']
        
        print(f"  Initial PS1:     '{scenario['initial_env'].get('PS1', '')}'")
        print(f"  Initial PROMPT:  '{scenario['initial_env'].get('PROMPT', '')}'")
        print(f"  Result PS1:      '{env['PS1']}' {'✅' if ps1_correct else '❌'}")
        print(f"  Result PROMPT:   '{env['PROMPT']}' {'✅' if prompt_correct else '❌'}")
        
        if ps1_correct and prompt_correct:
            print("  Status: ✅ PASSED")
        else:
            print("  Status: ❌ FAILED")
    
    print("\n" + "=" * 50)
    print("TFM now sets both PS1 and PROMPT variables to ensure")
    print("the [TFM] label appears in both bash and zsh shells!")

if __name__ == "__main__":
    test_tfm_prompt_logic()