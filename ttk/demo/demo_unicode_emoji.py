#!/usr/bin/env python3
"""
Demo: Unicode and Emoji Support

This demo showcases the CoreGraphics backend's support for:
- Unicode characters from various scripts
- Emoji rendering
- Complex scripts (Arabic, Thai, etc.)
- Automatic font fallback

Requirements demonstrated:
- 15.1: Unicode character support
- 15.2: Emoji rendering
- 15.3: Complex script support
- 15.4: Automatic font fallback

Usage:
    python demo_unicode_emoji.py
"""

import sys
import time

# Check if we're on macOS
if sys.platform != 'darwin':
    print("This demo requires macOS (CoreGraphics backend)")
    sys.exit(1)

# Try to import PyObjC
try:
    import Cocoa
except ImportError:
    print("PyObjC not available. Install with: pip install pyobjc-framework-Cocoa")
    sys.exit(1)

from ttk.backends.coregraphics_backend import CoreGraphicsBackend
from ttk.renderer import TextAttribute


def main():
    """Run the Unicode and emoji demo."""
    # Create backend with larger window for demo
    backend = CoreGraphicsBackend(
        window_title="TTK Unicode & Emoji Demo",
        rows=30,
        cols=80,
        font_size=12
    )
    
    try:
        backend.initialize()
        
        # Initialize color pairs
        backend.init_color_pair(1, (255, 255, 0), (0, 0, 128))    # Yellow on blue
        backend.init_color_pair(2, (0, 255, 0), (0, 0, 0))        # Green on black
        backend.init_color_pair(3, (255, 128, 0), (0, 0, 0))      # Orange on black
        backend.init_color_pair(4, (255, 0, 255), (0, 0, 0))      # Magenta on black
        backend.init_color_pair(5, (0, 255, 255), (0, 0, 0))      # Cyan on black
        
        # Clear screen
        backend.clear()
        
        # Title
        title = "═══ TTK Unicode & Emoji Support Demo ═══"
        backend.draw_text(0, (80 - len(title)) // 2, title, 
                         color_pair=1, attributes=TextAttribute.BOLD)
        
        # Section 1: Basic Unicode
        row = 2
        backend.draw_text(row, 0, "1. Unicode Characters:", 
                         color_pair=2, attributes=TextAttribute.BOLD)
        row += 1
        
        unicode_samples = [
            ("Latin:", "Héllo Wörld"),
            ("Cyrillic:", "Привет мир"),
            ("Chinese:", "你好世界"),
            ("Japanese:", "こんにちは世界"),
            ("Korean:", "안녕하세요"),
            ("Greek:", "Γειά σου κόσμε"),
            ("Hebrew:", "שלום עולם"),
        ]
        
        for label, text in unicode_samples:
            backend.draw_text(row, 2, f"{label:12} {text}", color_pair=0)
            row += 1
        
        # Section 2: Emoji
        row += 1
        backend.draw_text(row, 0, "2. Emoji Support:", 
                         color_pair=3, attributes=TextAttribute.BOLD)
        row += 1
        
        emoji_samples = [
            ("Smileys:", "😀😃😄😁😆😅😂🤣"),
            ("Hearts:", "❤️💙💚💛💜🖤🤍🤎"),
            ("Nature:", "🌍🌎🌏🌐🗺️🏔️🏕️"),
            ("Food:", "🍎🍊🍋🍌🍉🍇🍓"),
            ("Animals:", "🐶🐱🐭🐹🐰🦊🐻"),
            ("Tech:", "📱💻⌨️🖥️🖨️⌚"),
        ]
        
        for label, emoji in emoji_samples:
            backend.draw_text(row, 2, f"{label:12} {emoji}", color_pair=0)
            row += 1
        
        # Section 3: Complex Scripts
        row += 1
        backend.draw_text(row, 0, "3. Complex Scripts:", 
                         color_pair=4, attributes=TextAttribute.BOLD)
        row += 1
        
        complex_scripts = [
            ("Arabic:", "مرحبا بالعالم"),
            ("Thai:", "สวัสดีชาวโลก"),
            ("Hindi:", "नमस्ते दुनिया"),
            ("Tamil:", "வணக்கம் உலகம்"),
        ]
        
        for label, text in complex_scripts:
            backend.draw_text(row, 2, f"{label:12} {text}", color_pair=0)
            row += 1
        
        # Section 4: Special Characters
        row += 1
        backend.draw_text(row, 0, "4. Special Characters:", 
                         color_pair=5, attributes=TextAttribute.BOLD)
        row += 1
        
        backend.draw_text(row, 2, "Math:     ∑∫∂∇∞≈≠≤≥±×÷√", color_pair=0)
        row += 1
        backend.draw_text(row, 2, "Arrows:   ←↑→↓↔↕⇐⇑⇒⇓⇔⇕", color_pair=0)
        row += 1
        backend.draw_text(row, 2, "Symbols:  ★☆♠♣♥♦♪♫☺☻", color_pair=0)
        row += 1
        backend.draw_text(row, 2, "Box:      ┌─┐│└┘├┤┬┴┼", color_pair=0)
        row += 1
        
        # Section 5: Mixed Content
        row += 1
        backend.draw_text(row, 0, "5. Mixed Content (Font Fallback):", 
                         color_pair=2, attributes=TextAttribute.BOLD)
        row += 1
        
        mixed_samples = [
            "English + 中文 + العربية + 😀",
            "日本語 + 한국어 + Русский + 🌍",
            "Math: ∑∫∂ + Emoji: 🎉 + Greek: Ω",
        ]
        
        for text in mixed_samples:
            backend.draw_text(row, 2, text, color_pair=0)
            row += 1
        
        # Footer
        row = 28
        footer = "Press Ctrl+C to exit"
        backend.draw_text(row, (80 - len(footer)) // 2, footer, 
                         color_pair=0, attributes=TextAttribute.UNDERLINE)
        
        # Refresh to show everything
        backend.refresh()
        
        # Keep window open
        print("Demo running. Press Ctrl+C to exit.")
        try:
            while True:
                # Process events to keep window responsive
                event = backend.get_input(timeout_ms=100)
                if event:
                    # Exit on Escape key
                    from ttk.input_event import KeyCode
                    if event.key_code == KeyCode.ESCAPE:
                        break
        except KeyboardInterrupt:
            print("\nExiting demo...")
        
    finally:
        backend.shutdown()


if __name__ == '__main__':
    main()
