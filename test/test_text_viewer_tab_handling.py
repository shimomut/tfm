#!/usr/bin/env python3
"""
Test TAB character handling in text viewer with horizontal scrolling
"""

import sys
import os

# Add parent directory to path for imports
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


def test_tab_expansion():
    """Test that TAB characters are properly expanded to spaces"""
    
    # Create a test file with tabs
    test_file = Path("temp/test_tabs.txt")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write content with tabs at different positions
    content = "No tabs here\n"
    content += "One\ttab\there\n"
    content += "\tTab at start\n"
    content += "Multiple\t\ttabs\there\n"
    content += "Tab\tat\tevery\tword\n"
    
    test_file.write_text(content)
    
    try:
        # Create mock renderer
        renderer = MockRenderer(height=24, width=80)
        
        # Create text viewer
        viewer = TextViewer(renderer, test_file)
        
        # Verify tabs were expanded
        print("Testing TAB expansion:")
        print("-" * 60)
        
        for i, line in enumerate(viewer.lines):
            print(f"Line {i}: '{line}'")
            # Verify no tabs remain
            assert '\t' not in line, f"Line {i} still contains tabs: {repr(line)}"
        
        print("\n✓ All tabs successfully expanded to spaces")
        
        # Test that horizontal scrolling works with expanded tabs
        print("\nTesting horizontal scrolling with expanded tabs:")
        print("-" * 60)
        
        # Set horizontal offset
        viewer.horizontal_offset = 5
        
        # Draw content (this should not crash)
        viewer.draw_content()
        
        print("✓ Horizontal scrolling works with expanded tabs")
        
        # Test different tab widths
        print("\nTesting different tab widths:")
        print("-" * 60)
        
        for tab_width in [2, 4, 8]:
            viewer.tab_width = tab_width
            # Reload file with new tab width
            viewer.load_file()
            
            print(f"\nTab width = {tab_width}:")
            for i, line in enumerate(viewer.lines[:3]):  # Show first 3 lines
                print(f"  Line {i}: '{line}'")
                assert '\t' not in line, f"Line {i} contains tabs with tab_width={tab_width}"
        
        print("\n✓ All tab widths work correctly")
        
        return True
        
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()


def test_tab_column_alignment():
    """Test that tabs align to proper column positions"""
    
    test_file = Path("temp/test_tab_alignment.txt")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create content where tabs should align to specific columns
    # With tab_width=4, tabs should align to columns 0, 4, 8, 12, etc.
    content = "a\tb\tc\td\n"  # Should expand to "a   b   c   d"
    content += "ab\tcd\tef\n"  # Should expand to "ab  cd  ef"
    content += "abc\tdef\n"    # Should expand to "abc def"
    
    test_file.write_text(content)
    
    try:
        renderer = MockRenderer(height=24, width=80)
        viewer = TextViewer(renderer, test_file)
        viewer.tab_width = 4
        viewer.load_file()
        
        print("\nTesting TAB column alignment (tab_width=4):")
        print("-" * 60)
        
        # Line 0: "a\tb\tc\td" should become "a   b   c   d"
        # 'a' at col 0, tab to col 4, 'b' at col 4, tab to col 8, etc.
        expected_0 = "a   b   c   d"
        assert viewer.lines[0] == expected_0, f"Expected '{expected_0}', got '{viewer.lines[0]}'"
        print(f"Line 0: '{viewer.lines[0]}' ✓")
        
        # Line 1: "ab\tcd\tef" should become "ab  cd  ef"
        # 'ab' at cols 0-1, tab to col 4, 'cd' at cols 4-5, tab to col 8, 'ef' at cols 8-9
        expected_1 = "ab  cd  ef"
        assert viewer.lines[1] == expected_1, f"Expected '{expected_1}', got '{viewer.lines[1]}'"
        print(f"Line 1: '{viewer.lines[1]}' ✓")
        
        # Line 2: "abc\tdef" should become "abc def"
        # 'abc' at cols 0-2, tab to col 4, 'def' at cols 4-6
        expected_2 = "abc def"
        assert viewer.lines[2] == expected_2, f"Expected '{expected_2}', got '{viewer.lines[2]}'"
        print(f"Line 2: '{viewer.lines[2]}' ✓")
        
        print("\n✓ TAB column alignment is correct")
        
        return True
        
    finally:
        if test_file.exists():
            test_file.unlink()


if __name__ == '__main__':
    print("=" * 60)
    print("Text Viewer TAB Handling Test")
    print("=" * 60)
    
    try:
        test_tab_expansion()
        test_tab_column_alignment()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
