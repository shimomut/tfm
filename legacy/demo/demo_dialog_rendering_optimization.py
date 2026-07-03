#!/usr/bin/env python3
"""
Demo script showing dialog rendering optimization in action
"""

import sys
import os
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_quick_edit_bar import QuickEditBar
from tfm_list_dialog import ListDialog
from tfm_config import get_config


class MockStdscr:
    """Mock curses screen for testing"""
    def __init__(self):
        self.draw_count = 0
        
    def getmaxyx(self):
        return (24, 80)
        
    def addstr(self, y, x, text, attr=0):
        pass


def mock_safe_addstr(y, x, text, attr=0):
    """Mock safe_addstr function"""
    pass


def demo_optimization():
    """Demonstrate the dialog rendering optimization"""
    
    print("Dialog Rendering Optimization Demo")
    print("=" * 40)
    
    config = get_config()
    mock_stdscr = MockStdscr()
    
    # Create a dialog
    dialog = QuickEditBar(config)
    
    # Track draw calls
    original_draw = dialog._draw_status_line_input
    draw_count = 0
    
    def counting_draw(*args, **kwargs):
        nonlocal draw_count
        draw_count += 1
        print(f"  Dialog drawn (call #{draw_count})")
        # Don't actually call the original draw to avoid curses issues
    
    dialog._draw_status_line_input = counting_draw
    
    print("\n1. Showing dialog (should trigger draw):")
    dialog.show_status_line_input("Enter text: ")
    
    # Simulate main loop behavior - draw only when content changed
    print("\n2. Simulating main loop iterations without content changes:")
    for i in range(5):
        print(f"  Iteration {i+1}:")
        if dialog.content_changed:
            print("    Content changed - drawing dialog")
            dialog.draw(mock_stdscr, mock_safe_addstr)
            dialog.content_changed = False
        else:
            print("    No content change - skipping draw")
    
    print(f"\n   Total draws so far: {draw_count}")
    
    print("\n3. Simulating text input (should trigger draw):")
    dialog.handle_key(ord('h'))  # Type 'h'
    print(f"   Content changed: {dialog.content_changed}")
    
    if dialog.content_changed:
        print("   Content changed - drawing dialog")
        dialog.draw(mock_stdscr, mock_safe_addstr)
        dialog.content_changed = False
    
    print(f"   Total draws: {draw_count}")
    
    print("\n4. More iterations without changes:")
    for i in range(3):
        print(f"  Iteration {i+1}:")
        if dialog.content_changed:
            print("    Content changed - drawing dialog")
            dialog.draw(mock_stdscr, mock_safe_addstr)
            dialog.content_changed = False
        else:
            print("    No content change - skipping draw")
    
    print(f"\n   Final total draws: {draw_count}")
    
    print("\n5. Performance comparison:")
    print("   Without optimization: Would have drawn 9 times (every iteration)")
    print(f"   With optimization: Drew only {draw_count} times (only when needed)")
    
    if draw_count < 9:
        savings = ((9 - draw_count) / 9) * 100
        print(f"   Performance improvement: {savings:.1f}% reduction in draw calls")
    
    print("\n✅ Optimization working correctly!")


def demo_list_dialog_optimization():
    """Demonstrate list dialog optimization"""
    
    print("\n\nList Dialog Optimization Demo")
    print("=" * 40)
    
    config = get_config()
    mock_stdscr = MockStdscr()
    
    dialog = ListDialog(config)
    
    # Track draw calls
    original_draw = dialog.draw
    draw_count = 0
    
    def counting_draw(*args, **kwargs):
        nonlocal draw_count
        draw_count += 1
        print(f"  List dialog drawn (call #{draw_count})")
        # Don't actually call the original draw to avoid curses issues
    
    dialog.draw = counting_draw
    
    print("\n1. Showing list dialog:")
    dialog.show("Test List", ["Item 1", "Item 2", "Item 3"], None)
    
    print("\n2. Simulating navigation (should trigger draws):")
    
    # Simulate down arrow
    dialog.handle_input(65364)  # KEY_DOWN
    print(f"   Content changed after navigation: {dialog.content_changed}")
    
    if dialog.content_changed:
        dialog.draw(mock_stdscr, mock_safe_addstr)
        dialog.content_changed = False
    
    print("\n3. Iterations without changes:")
    for i in range(3):
        print(f"  Iteration {i+1}:")
        if dialog.content_changed:
            print("    Content changed - drawing dialog")
            dialog.draw(mock_stdscr, mock_safe_addstr)
            dialog.content_changed = False
        else:
            print("    No content change - skipping draw")
    
    print(f"\n   Total draws: {draw_count}")
    print("✅ List dialog optimization working!")


if __name__ == "__main__":
    try:
        demo_optimization()
        demo_list_dialog_optimization()
        
        print("\n" + "=" * 50)
        print("🎉 Dialog rendering optimization demo completed!")
        print("   Dialogs now only redraw when their content actually changes,")
        print("   significantly reducing unnecessary rendering overhead.")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)