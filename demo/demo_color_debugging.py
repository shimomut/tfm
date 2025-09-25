#!/usr/bin/env python3
"""
Demo script for TFM color debugging functionality

This script demonstrates how to use the new --color-test feature to diagnose
color rendering issues across different terminals and environments.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_demo():
    """Run the color debugging demo"""
    print("TFM Color Debugging Demo")
    print("=" * 40)
    print()
    
    # Get the path to tfm.py
    tfm_script = Path(__file__).parent.parent / 'tfm.py'
    
    if not tfm_script.exists():
        print("Error: tfm.py not found!")
        return
    
    print("This demo shows how to use TFM's color debugging features.")
    print("The --color-test argument provides several modes to help diagnose")
    print("color rendering issues between different laptops/terminals.")
    print()
    
    # Show available modes
    print("Available color test modes:")
    print("  info         - Show basic color and terminal information")
    print("  schemes      - List all available color schemes with details")
    print("  capabilities - Test terminal color support capabilities")
    print("  rgb-test     - Test RGB color functionality (forces RGB mode)")
    print("  fallback-test- Test fallback color functionality (forces fallback)")
    print("  interactive  - Interactive color tester with live preview")
    print()
    
    # Demonstrate each mode
    modes = [
        ('info', 'Basic Information'),
        ('schemes', 'Color Schemes'),
        ('capabilities', 'Terminal Capabilities (requires curses)'),
    ]
    
    for mode, description in modes:
        print(f"Running: {description}")
        print("-" * 30)
        
        try:
            if mode == 'capabilities':
                print("Note: This test requires a terminal and may not work in all environments.")
                print("If it hangs, press Ctrl+C to continue.")
                print()
            
            result = subprocess.run([
                sys.executable, str(tfm_script), '--color-test', mode
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(result.stdout)
            else:
                print(f"Error running {mode} test:")
                print(result.stderr)
                
        except subprocess.TimeoutExpired:
            print(f"Test {mode} timed out (this is normal for interactive tests)")
        except Exception as e:
            print(f"Error running {mode} test: {e}")
        
        print()
        input("Press Enter to continue to next test...")
        print()
    
    # Show usage examples
    print("Usage Examples:")
    print("=" * 20)
    print()
    
    examples = [
        ("python tfm.py --color-test info", 
         "Get basic color information without starting TFM"),
        
        ("python tfm.py --color-test schemes", 
         "See all available color schemes and their RGB values"),
        
        ("python tfm.py --color-test capabilities", 
         "Test what color features your terminal supports"),
        
        ("python tfm.py --color-test rgb-test", 
         "Force RGB mode to test if RGB colors work"),
        
        ("python tfm.py --color-test fallback-test", 
         "Force fallback mode to test basic color compatibility"),
        
        ("python tfm.py --color-test interactive", 
         "Interactive tester - switch between schemes and modes live"),
    ]
    
    for command, description in examples:
        print(f"Command: {command}")
        print(f"Purpose: {description}")
        print()
    
    print("Troubleshooting Tips:")
    print("=" * 20)
    print()
    
    tips = [
        "If colors don't work on one laptop but work on another:",
        "  1. Run 'python tfm.py --color-test capabilities' on both",
        "  2. Compare the RGB support and color count",
        "  3. Check TERM and COLORTERM environment variables",
        "  4. Try 'python tfm.py --color-test fallback-test' to see basic colors",
        "",
        "If you see only black and white:",
        "  1. Your terminal may not support colors at all",
        "  2. Try setting TERM=xterm-256color",
        "  3. Use the interactive tester to try different modes",
        "",
        "If RGB colors don't work but basic colors do:",
        "  1. Your terminal supports 8/16 colors but not RGB",
        "  2. TFM will automatically use fallback colors",
        "  3. This is normal for many terminal emulators",
        "",
        "Environment variables that affect colors:",
        "  TERM - Terminal type (xterm, xterm-256color, etc.)",
        "  COLORTERM - Color support indicator (truecolor, 24bit, etc.)",
        "  TERM_PROGRAM - Terminal application name",
    ]
    
    for tip in tips:
        print(tip)
    
    print()
    print("Demo completed!")
    print()
    print("To run the interactive color tester:")
    print(f"python {tfm_script} --color-test interactive")

if __name__ == "__main__":
    run_demo()