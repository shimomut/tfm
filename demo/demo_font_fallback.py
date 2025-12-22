#!/usr/bin/env python3
"""
Demo: Cascade Font Configuration

Demonstrates the cascade font feature in desktop mode configuration.
Shows how DESKTOP_FONT_NAME can be a list of fonts for automatic character fallback.

The first font in the list is the primary font, and remaining fonts are cascade
fonts used automatically when the primary font doesn't have a character.

Usage:
    python3 demo/demo_font_fallback.py
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def demo_cascade_fonts():
    """Demonstrate cascade font configuration"""
    print("=" * 70)
    print("Cascade Font Configuration Demo")
    print("=" * 70)
    print()
    
    print("DESKTOP_FONT_NAME can be configured as a list of fonts.")
    print("The first font is the primary font, and remaining fonts are")
    print("cascade fonts used automatically for character fallback.")
    print()
    
    # Example configurations
    examples = [
        {
            'name': 'Single font (backward compatible)',
            'config': "DESKTOP_FONT_NAME = 'Menlo'",
            'description': 'Uses Menlo for all characters'
        },
        {
            'name': 'Western fonts with fallbacks',
            'config': "DESKTOP_FONT_NAME = ['SF Mono', 'Menlo', 'Monaco', 'Courier']",
            'description': 'Primary: SF Mono, Cascade: Menlo → Monaco → Courier'
        },
        {
            'name': 'Western + CJK support',
            'config': "DESKTOP_FONT_NAME = ['Menlo', 'Monaco', 'Osaka-Mono', 'Hiragino Sans GB']",
            'description': 'Primary: Menlo, Cascade: Monaco → Osaka-Mono (Japanese) → Hiragino Sans GB (Chinese)'
        },
        {
            'name': 'Comprehensive international support',
            'config': "DESKTOP_FONT_NAME = ['SF Mono', 'Menlo', 'Courier', 'Osaka-Mono', 'Hiragino Sans GB']",
            'description': 'Western fonts first, then Japanese and Chinese support'
        },
    ]
    
    print("Configuration Examples:")
    print("-" * 70)
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['name']}")
        print(f"   {example['config']}")
        print(f"   {example['description']}")
    
    print("\n" + "=" * 70)
    print("How Cascade Fonts Work")
    print("=" * 70)
    print()
    print("When rendering text:")
    print("  1. Try to render character with primary font (first in list)")
    print("  2. If character not available, try first cascade font")
    print("  3. If still not available, try next cascade font")
    print("  4. Continue until character is found or all fonts exhausted")
    print()
    print("Example with ['Menlo', 'Osaka-Mono']:")
    print("  • 'Hello' → Rendered with Menlo (has Latin characters)")
    print("  • '日本語' → Rendered with Osaka-Mono (Menlo lacks Japanese)")
    print("  • Mixed text seamlessly uses both fonts as needed")
    print()
    
    print("=" * 70)
    print("Configuration in ~/.tfm/config.py")
    print("=" * 70)
    print()
    print("Example configuration:")
    print()
    print("class Config:")
    print("    # Desktop mode settings with CJK support")
    print("    DESKTOP_FONT_NAME = [")
    print("        'Menlo',           # Primary font (Western)")
    print("        'Monaco',          # Fallback (Western)")
    print("        'Courier',         # Universal fallback")
    print("        'Osaka-Mono',      # Japanese characters")
    print("        'Hiragino Sans GB' # Chinese characters")
    print("    ]")
    print("    DESKTOP_FONT_SIZE = 14")
    print()
    print("Benefits:")
    print("  • Automatic character fallback (no manual font selection)")
    print("  • Support for international characters (CJK, etc.)")
    print("  • Seamless rendering of mixed-language text")
    print("  • Backward compatible (single string still works)")
    print("  • C++ renderer handles all cascade logic efficiently")
    print()
    
    print("=" * 70)
    print("Testing Your Configuration")
    print("=" * 70)
    print()
    print("To test your font configuration:")
    print("  1. Edit ~/.tfm/config.py with your desired font list")
    print("  2. Run TFM in desktop mode: python3 tfm.py --desktop")
    print("  3. Navigate to files with international characters")
    print("  4. Verify characters render correctly")
    print()
    print("Common CJK fonts on macOS:")
    print("  • Japanese: Osaka-Mono, Hiragino Sans, Hiragino Kaku Gothic")
    print("  • Chinese: Hiragino Sans GB, PingFang SC, STHeiti")
    print("  • Korean: AppleGothic, Apple SD Gothic Neo")
    print()


if __name__ == '__main__':
    demo_cascade_fonts()
