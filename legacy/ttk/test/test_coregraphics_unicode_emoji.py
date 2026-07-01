"""
Test Unicode and emoji support for CoreGraphics backend.

This test module verifies that the CoreGraphics backend correctly handles:
- Unicode characters from various scripts
- Emoji rendering
- Complex scripts (Arabic, Thai, etc.)
- Automatic font fallback for missing glyphs

Requirements tested:
- 15.1: Unicode character support
- 15.2: Emoji rendering
- 15.3: Complex script support
- 15.4: Automatic font fallback
"""

import sys
import pytest

# Check if we're on macOS
if sys.platform != 'darwin':
    pytest.skip("CoreGraphics backend only available on macOS", allow_module_level=True)

# Try to import PyObjC
try:
    import Cocoa
    COCOA_AVAILABLE = True
except ImportError:
    COCOA_AVAILABLE = False
    pytest.skip("PyObjC not available", allow_module_level=True)

from ttk.backends.coregraphics_backend import CoreGraphicsBackend


class TestUnicodeSupport:
    """Test Unicode character support (Requirement 15.1)."""
    
    def test_basic_unicode_characters(self):
        """Test rendering basic Unicode characters from various languages."""
        backend = CoreGraphicsBackend(
            window_title="Unicode Test",
            rows=10,
            cols=40
        )
        
        try:
            backend.initialize()
            
            # Test various Unicode characters
            test_strings = [
                "Hello World",           # ASCII baseline
                "Héllo Wörld",          # Latin with diacritics
                "Привет мир",           # Cyrillic
                "你好世界",              # Chinese
                "こんにちは世界",         # Japanese
                "안녕하세요",            # Korean
                "Γειά σου κόσμε",       # Greek
                "שלום עולם",            # Hebrew
            ]
            
            # Draw each test string on a different row
            for row, text in enumerate(test_strings):
                backend.draw_text(row, 0, text, color_pair=0)
            
            # Verify the characters are stored in the grid
            for row, text in enumerate(test_strings):
                for col, char in enumerate(text):
                    grid_char, _, _ = backend.grid[row][col]
                    assert grid_char == char, f"Character mismatch at ({row}, {col}): expected '{char}', got '{grid_char}'"
            
            # Trigger a refresh to ensure rendering doesn't crash
            backend.refresh()
            
        finally:
            backend.shutdown()
    
    def test_unicode_mathematical_symbols(self):
        """Test rendering Unicode mathematical symbols."""
        backend = CoreGraphicsBackend(
            window_title="Math Symbols Test",
            rows=5,
            cols=30
        )
        
        try:
            backend.initialize()
            
            # Mathematical symbols
            math_symbols = "∑∫∂∇∞≈≠≤≥±×÷√∛∜"
            backend.draw_text(0, 0, math_symbols, color_pair=0)
            
            # Verify storage
            for col, char in enumerate(math_symbols):
                grid_char, _, _ = backend.grid[0][col]
                assert grid_char == char
            
            backend.refresh()
            
        finally:
            backend.shutdown()
    
    def test_unicode_box_drawing_characters(self):
        """Test rendering Unicode box-drawing characters."""
        backend = CoreGraphicsBackend(
            window_title="Box Drawing Test",
            rows=5,
            cols=20
        )
        
        try:
            backend.initialize()
            
            # Box drawing characters (used by draw_rect)
            box_chars = "┌─┐│└┘├┤┬┴┼"
            backend.draw_text(0, 0, box_chars, color_pair=0)
            
            # Verify storage
            for col, char in enumerate(box_chars):
                grid_char, _, _ = backend.grid[0][col]
                assert grid_char == char
            
            backend.refresh()
            
        finally:
            backend.shutdown()
    
    def test_unicode_arrows_and_symbols(self):
        """Test rendering Unicode arrows and symbols."""
        backend = CoreGraphicsBackend(
            window_title="Arrows Test",
            rows=5,
            cols=30
        )
        
        try:
            backend.initialize()
            
            # Arrows and symbols
            arrows = "←↑→↓↔↕⇐⇑⇒⇓⇔⇕"
            symbols = "★☆♠♣♥♦♪♫☺☻"
            
            backend.draw_text(0, 0, arrows, color_pair=0)
            backend.draw_text(1, 0, symbols, color_pair=0)
            
            # Verify storage
            for col, char in enumerate(arrows):
                grid_char, _, _ = backend.grid[0][col]
                assert grid_char == char
            
            for col, char in enumerate(symbols):
                grid_char, _, _ = backend.grid[1][col]
                assert grid_char == char
            
            backend.refresh()
            
        finally:
            backend.shutdown()


class TestEmojiSupport:
    """Test emoji rendering (Requirement 15.2)."""
    
    def test_basic_emoji(self):
        """Test rendering basic emoji characters."""
        backend = CoreGraphicsBackend(
            window_title="Emoji Test",
            rows=10,
            cols=40
        )
        
        try:
            backend.initialize()
            
            # Test various emoji
            emoji_strings = [
                "😀😃😄😁😆😅",      # Smileys
                "❤️💙💚💛💜🖤",      # Hearts
                "🌍🌎🌏🌐🗺️",       # Globes and maps
                "🔥💧🌊⚡☀️",        # Elements
                "🎉🎊🎈🎁🎀",        # Celebrations
                "🍎🍊🍋🍌🍉",        # Fruits
                "🚗🚕🚙🚌🚎",        # Vehicles
                "📱💻⌨️🖥️🖨️",      # Technology
            ]
            
            # Draw each emoji string on a different row
            for row, emoji_text in enumerate(emoji_strings):
                backend.draw_text(row, 0, emoji_text, color_pair=0)
            
            # Verify the emoji are stored in the grid
            # Note: Some emoji may be multi-codepoint, so we just verify
            # that something was stored
            for row, emoji_text in enumerate(emoji_strings):
                grid_char, _, _ = backend.grid[row][0]
                assert grid_char != ' ', f"Expected emoji at row {row}, got space"
            
            # Trigger a refresh to ensure rendering doesn't crash
            backend.refresh()
            
        finally:
            backend.shutdown()
    
    def test_emoji_with_skin_tones(self):
        """Test rendering emoji with skin tone modifiers."""
        backend = CoreGraphicsBackend(
            window_title="Emoji Skin Tones Test",
            rows=5,
            cols=30
        )
        
        try:
            backend.initialize()
            
            # Emoji with different skin tones
            # Note: These are multi-codepoint sequences
            emoji_with_tones = "👋👋🏻👋🏼👋🏽👋🏾👋🏿"
            backend.draw_text(0, 0, emoji_with_tones, color_pair=0)
            
            # Just verify that something was stored (multi-codepoint handling)
            grid_char, _, _ = backend.grid[0][0]
            assert grid_char != ' '
            
            backend.refresh()
            
        finally:
            backend.shutdown()
    
    def test_emoji_flags(self):
        """Test rendering emoji flags."""
        backend = CoreGraphicsBackend(
            window_title="Emoji Flags Test",
            rows=5,
            cols=30
        )
        
        try:
            backend.initialize()
            
            # Country flags (these are regional indicator sequences)
            flags = "🇺🇸🇬🇧🇫🇷🇩🇪🇯🇵🇨🇳🇰🇷"
            backend.draw_text(0, 0, flags, color_pair=0)
            
            # Just verify that something was stored
            grid_char, _, _ = backend.grid[0][0]
            assert grid_char != ' '
            
            backend.refresh()
            
        finally:
            backend.shutdown()


class TestComplexScripts:
    """Test complex script support (Requirement 15.3)."""
    
    def test_arabic_script(self):
        """Test rendering Arabic script (right-to-left)."""
        backend = CoreGraphicsBackend(
            window_title="Arabic Test",
            rows=5,
            cols=40
        )
        
        try:
            backend.initialize()
            
            # Arabic text (right-to-left)
            arabic_text = "مرحبا بالعالم"  # "Hello World" in Arabic
            backend.draw_text(0, 0, arabic_text, color_pair=0)
            
            # Verify characters are stored
            for col, char in enumerate(arabic_text):
                grid_char, _, _ = backend.grid[0][col]
                assert grid_char == char
            
            backend.refresh()
            
        finally:
            backend.shutdown()
    
    def test_thai_script(self):
        """Test rendering Thai script (complex combining characters)."""
        backend = CoreGraphicsBackend(
            window_title="Thai Test",
            rows=5,
            cols=40
        )
        
        try:
            backend.initialize()
            
            # Thai text with combining characters
            thai_text = "สวัสดีชาวโลก"  # "Hello World" in Thai
            backend.draw_text(0, 0, thai_text, color_pair=0)
            
            # Verify characters are stored
            for col, char in enumerate(thai_text):
                grid_char, _, _ = backend.grid[0][col]
                assert grid_char == char
            
            backend.refresh()
            
        finally:
            backend.shutdown()
    
    def test_devanagari_script(self):
        """Test rendering Devanagari script (Hindi)."""
        backend = CoreGraphicsBackend(
            window_title="Devanagari Test",
            rows=5,
            cols=40
        )
        
        try:
            backend.initialize()
            
            # Hindi text in Devanagari script
            hindi_text = "नमस्ते दुनिया"  # "Hello World" in Hindi
            backend.draw_text(0, 0, hindi_text, color_pair=0)
            
            # Verify characters are stored
            for col, char in enumerate(hindi_text):
                grid_char, _, _ = backend.grid[0][col]
                assert grid_char == char
            
            backend.refresh()
            
        finally:
            backend.shutdown()
    
    def test_tamil_script(self):
        """Test rendering Tamil script."""
        backend = CoreGraphicsBackend(
            window_title="Tamil Test",
            rows=5,
            cols=40
        )
        
        try:
            backend.initialize()
            
            # Tamil text
            tamil_text = "வணக்கம் உலகம்"  # "Hello World" in Tamil
            backend.draw_text(0, 0, tamil_text, color_pair=0)
            
            # Verify characters are stored
            for col, char in enumerate(tamil_text):
                grid_char, _, _ = backend.grid[0][col]
                assert grid_char == char
            
            backend.refresh()
            
        finally:
            backend.shutdown()


class TestFontFallback:
    """Test automatic font fallback (Requirement 15.4)."""
    
    def test_mixed_scripts_font_fallback(self):
        """Test that mixed scripts work together (relies on font fallback)."""
        backend = CoreGraphicsBackend(
            window_title="Font Fallback Test",
            rows=10,
            cols=50
        )
        
        try:
            backend.initialize()
            
            # Mix of different scripts that likely require different fonts
            mixed_text = [
                "English + 中文 + العربية",
                "日本語 + 한국어 + Русский",
                "Ελληνικά + עברית + ไทย",
                "Math: ∑∫∂ + Emoji: 😀🌍",
            ]
            
            # Draw mixed text
            for row, text in enumerate(mixed_text):
                backend.draw_text(row, 0, text, color_pair=0)
            
            # Verify all characters are stored
            for row, text in enumerate(mixed_text):
                for col, char in enumerate(text):
                    grid_char, _, _ = backend.grid[row][col]
                    assert grid_char == char
            
            # Trigger refresh - this tests that CoreText handles font fallback
            backend.refresh()
            
        finally:
            backend.shutdown()
    
    def test_rare_unicode_characters(self):
        """Test rendering rare Unicode characters (tests font fallback)."""
        backend = CoreGraphicsBackend(
            window_title="Rare Unicode Test",
            rows=5,
            cols=40
        )
        
        try:
            backend.initialize()
            
            # Some less common Unicode characters
            rare_chars = "Ⓐⓑⓒ①②③ⅠⅡⅢ㊀㊁㊂"
            backend.draw_text(0, 0, rare_chars, color_pair=0)
            
            # Verify storage
            for col, char in enumerate(rare_chars):
                grid_char, _, _ = backend.grid[0][col]
                assert grid_char == char
            
            backend.refresh()
            
        finally:
            backend.shutdown()
    
    def test_unicode_with_attributes(self):
        """Test Unicode characters with text attributes."""
        backend = CoreGraphicsBackend(
            window_title="Unicode Attributes Test",
            rows=5,
            cols=40
        )
        
        try:
            backend.initialize()
            backend.init_color_pair(1, (255, 255, 0), (0, 0, 255))
            
            # Unicode text with attributes
            from ttk.renderer import TextAttribute
            
            unicode_text = "Hello 世界 🌍"
            backend.draw_text(0, 0, unicode_text, color_pair=1, 
                            attributes=TextAttribute.BOLD)
            backend.draw_text(1, 0, unicode_text, color_pair=1,
                            attributes=TextAttribute.UNDERLINE)
            backend.draw_text(2, 0, unicode_text, color_pair=1,
                            attributes=TextAttribute.REVERSE)
            
            # Verify storage with attributes
            for col, char in enumerate(unicode_text):
                grid_char, color, attrs = backend.grid[0][col]
                assert grid_char == char
                assert color == 1
                assert attrs == TextAttribute.BOLD
            
            backend.refresh()
            
        finally:
            backend.shutdown()


class TestUnicodeEdgeCases:
    """Test edge cases for Unicode handling."""
    
    def test_zero_width_characters(self):
        """Test handling of zero-width characters."""
        backend = CoreGraphicsBackend(
            window_title="Zero Width Test",
            rows=5,
            cols=40
        )
        
        try:
            backend.initialize()
            
            # Text with zero-width joiner (used in emoji sequences)
            text_with_zwj = "👨‍👩‍👧‍👦"  # Family emoji with ZWJ
            backend.draw_text(0, 0, text_with_zwj, color_pair=0)
            
            # Just verify something was stored
            grid_char, _, _ = backend.grid[0][0]
            assert grid_char != ' '
            
            backend.refresh()
            
        finally:
            backend.shutdown()
    
    def test_combining_diacritics(self):
        """Test handling of combining diacritical marks."""
        backend = CoreGraphicsBackend(
            window_title="Combining Marks Test",
            rows=5,
            cols=40
        )
        
        try:
            backend.initialize()
            
            # Text with combining diacritics
            # e + combining acute accent
            text_with_combining = "e\u0301"  # é composed with combining mark
            backend.draw_text(0, 0, text_with_combining, color_pair=0)
            
            # Verify storage (may store as separate characters)
            grid_char, _, _ = backend.grid[0][0]
            assert grid_char in ['e', 'é']  # Either the base or composed form
            
            backend.refresh()
            
        finally:
            backend.shutdown()
    
    def test_long_unicode_string(self):
        """Test rendering a long string with mixed Unicode."""
        backend = CoreGraphicsBackend(
            window_title="Long Unicode Test",
            rows=5,
            cols=80
        )
        
        try:
            backend.initialize()
            
            # Long mixed Unicode string
            long_text = "Hello世界🌍Привет мир你好こんにちは안녕하세요Γειά σου שלום مرحبا"
            backend.draw_text(0, 0, long_text, color_pair=0)
            
            # Verify characters up to grid width
            for col, char in enumerate(long_text[:backend.cols]):
                grid_char, _, _ = backend.grid[0][col]
                assert grid_char == char
            
            backend.refresh()
            
        finally:
            backend.shutdown()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
