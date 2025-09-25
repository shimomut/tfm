#!/usr/bin/env python3
"""
Fix for color pair limitation (32767) that causes color issues

This script provides solutions for terminals that have the 32767 color pair
limitation which can interfere with RGB color initialization.
"""

import sys
import os
import curses
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_dir))

def test_color_pair_limitation():
    """Test if the terminal has the 32767 color pair limitation"""
    def test_limitation(stdscr):
        caps = {}
        try:
            caps['colors'] = curses.COLORS
            caps['color_pairs'] = curses.COLOR_PAIRS
            caps['can_change_color'] = curses.can_change_color()
        except:
            caps['colors'] = 8
            caps['color_pairs'] = 64
            caps['can_change_color'] = False
        
        return caps
    
    try:
        return curses.wrapper(test_limitation)
    except Exception as e:
        print(f"Error testing color capabilities: {e}")
        return {'colors': 8, 'color_pairs': 64, 'can_change_color': False}

def create_optimized_color_scheme():
    """Create an optimized color scheme for limited color pair terminals"""
    
    # This is a simplified color scheme that uses fewer color pairs
    # and relies more on basic terminal colors
    
    optimized_scheme = """
# Optimized TFM Color Configuration for Limited Color Pair Terminals
# Place this in your TFM config to work around 32767 color pair limitation

# Use fallback colors even if RGB is supported
FORCE_FALLBACK_COLORS = True

# Use basic color scheme
COLOR_SCHEME = 'dark'

# Reduce color complexity
SEPARATE_EXTENSIONS = False  # Reduces color pair usage
"""
    
    return optimized_scheme

def apply_color_pair_fix():
    """Apply fixes for color pair limitation"""
    print("TFM Color Pair Limitation Fix")
    print("=" * 40)
    print()
    
    # Test current capabilities
    caps = test_color_pair_limitation()
    color_pairs = caps.get('color_pairs', 0)
    colors = caps.get('colors', 0)
    rgb_support = caps.get('can_change_color', False)
    
    print(f"Current terminal capabilities:")
    print(f"  Colors: {colors}")
    print(f"  Color pairs: {color_pairs}")
    print(f"  RGB support: {rgb_support}")
    print()
    
    if color_pairs == 32767:
        print("🔍 DETECTED: 32767 color pair limitation")
        print()
        print("This limitation can cause RGB color initialization to fail.")
        print("Applying fixes...")
        print()
        
        # Solution 1: Force fallback colors
        print("Solution 1: Force fallback color mode")
        print("-" * 35)
        print("This forces TFM to use basic terminal colors instead of RGB.")
        print()
        print("To apply this fix:")
        print("1. Run: python tfm.py --color-test fallback-test")
        print("2. If colors work, add this to your TFM config:")
        print("   FORCE_FALLBACK_COLORS = True")
        print()
        
        # Solution 2: Environment variables
        print("Solution 2: Environment variable fixes")
        print("-" * 37)
        print("Try these environment variables:")
        print("  export TERM=xterm-256color")
        print("  export COLORTERM=256color")
        print("  # OR")
        print("  export TERM=screen-256color")
        print()
        
        # Solution 3: Terminal-specific fixes
        print("Solution 3: Terminal-specific fixes")
        print("-" * 35)
        
        term_program = os.environ.get('TERM_PROGRAM', 'unknown')
        term = os.environ.get('TERM', 'unknown')
        
        if 'screen' in term.lower():
            print("Screen/tmux detected:")
            print("  - Add to ~/.screenrc: termcapinfo xterm 'Co#256:AB=\\E[48;5;%dm:AF=\\E[38;5;%dm'")
            print("  - Or use: screen -T xterm-256color")
            
        elif 'xterm' in term.lower():
            print("Xterm detected:")
            print("  - Try: export TERM=xterm-256color")
            print("  - Check xterm color support: xterm -report-colors")
            
        else:
            print(f"Terminal: {term_program} / {term}")
            print("  - Try different TERM values: xterm-256color, screen-256color")
            print("  - Check terminal documentation for color support")
        
        print()
        
        # Solution 4: Create optimized config
        print("Solution 4: Optimized configuration")
        print("-" * 35)
        
        config_path = Path.home() / '.tfm' / 'config.py'
        print(f"Create optimized config at: {config_path}")
        print()
        
        optimized_config = create_optimized_color_scheme()
        print("Optimized configuration:")
        print(optimized_config)
        
        # Test the fixes
        print("Testing fixes:")
        print("-" * 15)
        print("Run these tests to verify fixes:")
        print("1. python tfm.py --color-test color-pairs")
        print("2. python tfm.py --color-test fallback-test")
        print("3. python tfm.py --color-test interactive")
        print("4. python tfm.py  # Test main application")
        
    elif color_pairs >= 65536:
        print("✅ Good: No color pair limitation detected")
        print("Your terminal supports high color pair counts.")
        print("The color issue is likely caused by something else.")
        print()
        print("Try these diagnostic tools:")
        print("- python tfm.py --color-test diagnose")
        print("- python tools/test_stdout_color_issue.py")
        
    else:
        print(f"⚠️  Moderate color pair count: {color_pairs}")
        print("This might cause issues with complex color schemes.")
        print()
        print("Recommended fixes:")
        print("1. Use fallback color mode")
        print("2. Try different terminal emulator")
        print("3. Set TERM=xterm-256color")

def main():
    """Main function"""
    print("Checking for color pair limitations...")
    print()
    
    apply_color_pair_fix()
    
    print()
    print("Summary:")
    print("- 32767 color pairs = limitation that needs workarounds")
    print("- 65536+ color pairs = good, no limitation")
    print("- <64 color pairs = very limited terminal")
    print()
    print("For immediate testing:")
    print("python tfm.py --color-test color-pairs")

if __name__ == "__main__":
    main()