"""
Test script for text viewer tab width feature.

This test verifies that the tab width can be changed dynamically
and that tabs are expanded correctly with different widths.

Run with: PYTHONPATH=.:src:ttk pytest test/test_text_viewer_tab_width.py -v
"""

import os
from tfm_text_viewer import TextViewer
from tfm_path import Path
from ttk import KeyEvent, KeyCode
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


def create_test_file_with_tabs(file_path: str):
    """Create a test file with tab characters"""
    content = """# Test file with tabs
def function():
\tif True:
\t\tprint("Hello")
\t\tfor i in range(10):
\t\t\tprint(i)

class MyClass:
\tdef __init__(self):
\t\tself.value = 42
\t
\tdef method(self):
\t\treturn self.value
"""
    with open(file_path, 'w') as f:
        f.write(content)


def test_tab_width_change():
    """Test changing tab width"""
    print("Testing tab width change feature...")
    
    # Create test file
    test_file = "temp/test_tabs.py"
    os.makedirs("temp", exist_ok=True)
    create_test_file_with_tabs(test_file)
    
    try:
        # Create viewer
        renderer = MockRenderer(height=24, width=80)
        viewer = TextViewer(renderer, Path(test_file))
        
        # Test initial tab width (should be 4)
        print(f"Initial tab width: {viewer.tab_width}")
        assert viewer.tab_width == 4, f"Expected initial tab width 4, got {viewer.tab_width}"
        
        # Check that tabs are expanded in the loaded lines
        # Line with single tab should have 4 spaces
        line_with_tab = viewer.lines[2]  # "if True:" line
        print(f"Line with single tab: '{line_with_tab}'")
        assert line_with_tab.startswith("    "), "Single tab should expand to 4 spaces"
        
        # Simulate pressing 't' to change tab width to 8
        event = KeyEvent(char='t', key_code=None)
        viewer.handle_input(event)
        
        print(f"Tab width after first 't' press: {viewer.tab_width}")
        assert viewer.tab_width == 8, f"Expected tab width 8, got {viewer.tab_width}"
        
        # Check that tabs are now expanded to 8 spaces
        line_with_tab = viewer.lines[2]
        print(f"Line with single tab (8 spaces): '{line_with_tab}'")
        assert line_with_tab.startswith("        "), "Single tab should expand to 8 spaces"
        
        # Simulate pressing 't' again to change tab width to 2
        event = KeyEvent(char='t', key_code=None)
        viewer.handle_input(event)
        
        print(f"Tab width after second 't' press: {viewer.tab_width}")
        assert viewer.tab_width == 2, f"Expected tab width 2, got {viewer.tab_width}"
        
        # Check that tabs are now expanded to 2 spaces
        line_with_tab = viewer.lines[2]
        print(f"Line with single tab (2 spaces): '{line_with_tab}'")
        assert line_with_tab.startswith("  "), "Single tab should expand to 2 spaces"
        
        # Simulate pressing 't' once more to cycle back to 4
        event = KeyEvent(char='t', key_code=None)
        viewer.handle_input(event)
        
        print(f"Tab width after third 't' press: {viewer.tab_width}")
        assert viewer.tab_width == 4, f"Expected tab width 4, got {viewer.tab_width}"
        
        print("✓ Tab width cycling works correctly")
        
        # Test that nested tabs work correctly
        line_with_three_tabs = viewer.lines[5]  # Line with 3 tabs
        print(f"Line with three tabs: '{line_with_three_tabs}'")
        # With tab_width=4, three tabs should be 12 spaces
        assert line_with_three_tabs.startswith("            "), "Three tabs should expand to 12 spaces"
        
        print("✓ Nested tabs expand correctly")
        
        print("\n✅ All tab width tests passed!")
        
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)


def test_tab_width_display():
    """Test that tab width is displayed in status bar"""
    print("\nTesting tab width display in status bar...")
    
    # Create test file
    test_file = "temp/test_tabs_display.py"
    os.makedirs("temp", exist_ok=True)
    create_test_file_with_tabs(test_file)
    
    try:
        # Create viewer
        renderer = MockRenderer(height=24, width=80)
        viewer = TextViewer(renderer, Path(test_file))
        
        # Draw status bar
        viewer.draw_status_bar()
        
        # Check that the renderer has drawn text containing "TAB:4"
        drawn_text = renderer.get_drawn_text()
        print(f"Status bar content: {drawn_text}")
        
        # Look for TAB:4 in the drawn text
        found_tab_indicator = False
        for text, _, _ in drawn_text:
            if "TAB:4" in text:
                found_tab_indicator = True
                break
        
        assert found_tab_indicator, "Status bar should display TAB:4"
        print("✓ Tab width is displayed in status bar")
        
        # Change tab width and check display
        event = KeyEvent(char='t', key_code=None)
        viewer.handle_input(event)
        
        renderer.clear_drawn_text()
        viewer.draw_status_bar()
        drawn_text = renderer.get_drawn_text()
        
        found_tab_indicator = False
        for text, _, _ in drawn_text:
            if "TAB:8" in text:
                found_tab_indicator = True
                break
        
        assert found_tab_indicator, "Status bar should display TAB:8 after change"
        print("✓ Tab width display updates correctly")
        
        print("\n✅ All tab width display tests passed!")
        
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)


def test_tab_expansion_alignment():
    """Test that tabs align correctly to tab stops"""
    print("\nTesting tab alignment to tab stops...")
    
    # Create test file with mixed content
    test_file = "temp/test_tab_alignment.txt"
    os.makedirs("temp", exist_ok=True)
    
    content = "a\tb\tc\n"  # Single chars separated by tabs
    content += "ab\tcd\tef\n"  # Two chars separated by tabs
    content += "abc\tdef\tghi\n"  # Three chars separated by tabs
    
    with open(test_file, 'w') as f:
        f.write(content)
    
    try:
        # Create viewer with tab_width=4
        renderer = MockRenderer(height=24, width=80)
        viewer = TextViewer(renderer, Path(test_file))
        
        # Check alignment with tab_width=4
        line1 = viewer.lines[0]
        line2 = viewer.lines[1]
        line3 = viewer.lines[2]
        
        print(f"Line 1: '{line1}'")
        print(f"Line 2: '{line2}'")
        print(f"Line 3: '{line3}'")
        
        # With tab_width=4:
        # "a\tb" -> "a   b" (a at col 0, tab fills to col 4, b at col 4)
        # "ab\tcd" -> "ab  cd" (ab at cols 0-1, tab fills to col 4, cd at col 4)
        # "abc\tdef" -> "abc def" (abc at cols 0-2, tab fills to col 4, def at col 4)
        
        assert line1 == "a   b   c", f"Expected 'a   b   c', got '{line1}'"
        assert line2 == "ab  cd  ef", f"Expected 'ab  cd  ef', got '{line2}'"
        assert line3 == "abc def ghi", f"Expected 'abc def ghi', got '{line3}'"
        
        print("✓ Tabs align correctly to tab stops")
        
        print("\n✅ All tab alignment tests passed!")
        
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
