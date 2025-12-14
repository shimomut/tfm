#!/usr/bin/env python3
"""
Test horizontal scroll behavior in text viewer
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_text_viewer import TextViewer
from tfm_path import Path
from ttk.renderer import TextAttribute


class MockRenderer:
    """Mock renderer for testing"""
    def __init__(self, height=24, width=80):
        self.height = height
        self.width = width
        self.drawn_text = []
        
    def get_dimensions(self):
        return self.height, self.width
        
    def draw_text(self, y, x, text, color_pair=0, attributes=TextAttribute.NORMAL):
        self.drawn_text.append({
            'y': y,
            'x': x,
            'text': text,
            'color_pair': color_pair,
            'attributes': attributes
        })
        
    def clear(self):
        self.drawn_text = []
        
    def refresh(self):
        pass


def test_horizontal_scroll():
    """Test horizontal scrolling with various offsets"""
    
    test_file = Path("temp/test_hscroll.txt")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a simple file with long lines - use unique characters
    content = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + "abcdefghijklmnopqrstuvwxyz" + "0123456789" * 5
    test_file.write_text(content)
    
    try:
        renderer = MockRenderer(height=10, width=40)
        viewer = TextViewer(renderer, test_file)
        viewer.show_line_numbers = False  # Disable for simpler testing
        viewer.syntax_highlighting = False  # Disable for simpler testing
        
        print("Testing horizontal scroll behavior:")
        print("=" * 60)
        print(f"Original line: {content[:50]}...")
        print(f"Line length: {len(content)} characters")
        print()
        
        # Test different horizontal offsets
        for offset in [0, 5, 10, 20, 30, 40]:
            viewer.horizontal_offset = offset
            renderer.clear()
            viewer.draw_content()
            
            # Find the actual content line (y=2 is where content starts, after header)
            content_draws = [d for d in renderer.drawn_text if d['y'] == 2 and d['text'].strip()]
            
            if content_draws:
                # Concatenate all text segments on the content line
                drawn = ''.join(d['text'] for d in content_draws)
                expected_start = content[offset:offset+40]
                
                # Verify the drawn text starts at the correct position
                match = "✓" if drawn.strip() == expected_start.strip() else "✗"
                print(f"Offset {offset:2d}: '{drawn[:40]}' {match}")
                
                if drawn.strip() != expected_start.strip():
                    print(f"           Expected: '{expected_start[:40]}'")
            else:
                print(f"Offset {offset:2d}: (no content drawn)")
        
        return True
        
    finally:
        if test_file.exists():
            test_file.unlink()


def test_horizontal_scroll_with_syntax():
    """Test horizontal scrolling with syntax highlighting enabled"""
    
    test_file = Path("temp/test_hscroll_syntax.py")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a Python file with long lines
    content = "# " + "This is a very long comment line " * 5
    test_file.write_text(content)
    
    try:
        renderer = MockRenderer(height=10, width=40)
        viewer = TextViewer(renderer, test_file)
        viewer.show_line_numbers = False
        viewer.syntax_highlighting = True  # Enable syntax highlighting
        
        print("\nTesting horizontal scroll with syntax highlighting:")
        print("=" * 60)
        print(f"Original line: {content[:50]}...")
        print()
        
        # Test different horizontal offsets
        for offset in [0, 10, 20, 30]:
            viewer.horizontal_offset = offset
            renderer.clear()
            viewer.draw_content()
            
            # Collect all drawn text segments
            content_draws = [d for d in renderer.drawn_text if d['text'].strip()]
            
            if content_draws:
                # Concatenate all segments
                drawn = ''.join(d['text'] for d in content_draws)
                print(f"Offset {offset:2d}: '{drawn[:40]}'")
            else:
                print(f"Offset {offset:2d}: (no content drawn)")
        
        return True
        
    finally:
        if test_file.exists():
            test_file.unlink()


if __name__ == '__main__':
    print("Horizontal Scroll Behavior Test")
    print("=" * 60)
    
    try:
        test_horizontal_scroll()
        test_horizontal_scroll_with_syntax()
        
        print("\n" + "=" * 60)
        print("Tests completed")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
