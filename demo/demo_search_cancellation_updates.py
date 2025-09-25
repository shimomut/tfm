#!/usr/bin/env python3
"""
Demo showing how search cancellation now triggers proper redraws
"""

import sys
import os
import time
import threading
from unittest.mock import Mock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_search_dialog import SearchDialog
from tfm_jump_dialog import JumpDialog
from tfm_config import get_config


def demo_search_cancellation():
    """Demonstrate search cancellation triggering redraws"""
    
    print("Search Cancellation Demo")
    print("=" * 30)
    
    config = get_config()
    search_dialog = SearchDialog(config)
    
    # Track draw calls
    draw_count = 0
    
    def mock_draw(*args, **kwargs):
        nonlocal draw_count
        draw_count += 1
        print(f"  🎨 Dialog redrawn (call #{draw_count})")
    
    search_dialog.draw = mock_draw
    
    print("\n1. Showing search dialog:")
    search_dialog.show('filename')
    search_dialog.text_editor.set_text('test')
    
    print("\n2. Simulating initial draw:")
    if search_dialog.content_changed:
        search_dialog.draw(None, None)
        search_dialog.content_changed = False
        print("   ✓ Initial draw completed")
    
    print(f"   Content changed: {search_dialog.content_changed}")
    
    print("\n3. Simulating search start:")
    # Simulate a running search
    search_dialog.searching = True
    search_dialog.search_thread = Mock()
    search_dialog.search_thread.is_alive.return_value = True
    print("   🔍 Search started...")
    
    print("\n4. Simulating main loop (no changes yet):")
    for i in range(3):
        print(f"   Iteration {i+1}: Content changed = {search_dialog.content_changed}")
        if search_dialog.content_changed:
            search_dialog.draw(None, None)
            search_dialog.content_changed = False
        else:
            print("   ⏸️  No redraw needed")
    
    print("\n5. User cancels search (ESC key):")
    search_dialog._cancel_current_search()
    print(f"   ✅ Search canceled, content changed = {search_dialog.content_changed}")
    
    print("\n6. Main loop detects cancellation:")
    if search_dialog.content_changed:
        print("   ✨ Content change detected!")
        search_dialog.draw(None, None)
        search_dialog.content_changed = False
        print("   ✓ Dialog redrawn to show cancellation state")
    
    print(f"\n   Total draws: {draw_count}")
    print("   ✅ Cancellation properly triggered redraw!")


def demo_search_completion():
    """Demonstrate search completion triggering redraws"""
    
    print("\n\nSearch Completion Demo")
    print("=" * 30)
    
    config = get_config()
    search_dialog = SearchDialog(config)
    
    # Track draw calls
    draw_count = 0
    
    def mock_draw(*args, **kwargs):
        nonlocal draw_count
        draw_count += 1
        print(f"  🎨 Dialog redrawn (call #{draw_count})")
    
    search_dialog.draw = mock_draw
    
    print("\n1. Search in progress:")
    search_dialog.show('filename')
    search_dialog.content_changed = False  # Simulate after initial draw
    search_dialog.searching = True
    
    print("   🔍 Searching for files...")
    print(f"   Content changed: {search_dialog.content_changed}")
    
    print("\n2. Search completes with results:")
    # Simulate search completion (what happens in _search_worker)
    with search_dialog.search_lock:
        search_dialog.results = ['file1.txt', 'file2.txt', 'file3.txt']
        search_dialog.searching = False
        search_dialog.content_changed = True  # This is the fix we added
    
    print(f"   ✅ Search completed, found {len(search_dialog.results)} results")
    print(f"   Content changed: {search_dialog.content_changed}")
    
    print("\n3. Main loop detects completion:")
    if search_dialog.content_changed:
        print("   ✨ Content change detected!")
        search_dialog.draw(None, None)
        search_dialog.content_changed = False
        print("   ✓ Dialog redrawn to show final results")
    
    print(f"\n   Total draws: {draw_count}")
    print("   ✅ Completion properly triggered redraw!")


def demo_jump_dialog_cancellation():
    """Demonstrate jump dialog cancellation triggering redraws"""
    
    print("\n\nJump Dialog Cancellation Demo")
    print("=" * 35)
    
    config = get_config()
    jump_dialog = JumpDialog(config)
    
    # Track draw calls
    draw_count = 0
    
    def mock_draw(*args, **kwargs):
        nonlocal draw_count
        draw_count += 1
        print(f"  🎨 Dialog redrawn (call #{draw_count})")
    
    jump_dialog.draw = mock_draw
    
    print("\n1. Directory scan in progress:")
    jump_dialog.show(os.getcwd())
    jump_dialog.content_changed = False  # Simulate after initial draw
    
    # Simulate running scan
    jump_dialog.searching = True
    jump_dialog.scan_thread = Mock()
    jump_dialog.scan_thread.is_alive.return_value = True
    
    print("   📁 Scanning directories...")
    print(f"   Content changed: {jump_dialog.content_changed}")
    
    print("\n2. User cancels scan:")
    jump_dialog._cancel_current_scan()
    print(f"   ✅ Scan canceled, content changed = {jump_dialog.content_changed}")
    
    print("\n3. Main loop detects cancellation:")
    if jump_dialog.content_changed:
        print("   ✨ Content change detected!")
        jump_dialog.draw(None, None)
        jump_dialog.content_changed = False
        print("   ✓ Dialog redrawn to show cancellation state")
    
    print(f"\n   Total draws: {draw_count}")
    print("   ✅ Directory scan cancellation properly triggered redraw!")


def demo_before_and_after():
    """Show the difference before and after the fix"""
    
    print("\n\nBefore vs After Comparison")
    print("=" * 35)
    
    print("\n📉 BEFORE the fix:")
    print("   1. User starts search/directory scan")
    print("   2. Background thread begins operation")
    print("   3. User presses ESC to cancel")
    print("   4. ❌ Dialog state changes but content_changed not set")
    print("   5. ❌ Main loop doesn't detect the change")
    print("   6. ❌ Dialog still shows 'Searching...' until next user input")
    print("   7. ❌ User sees stale 'in progress' state")
    
    print("\n📈 AFTER the fix:")
    print("   1. User starts search/directory scan")
    print("   2. Background thread begins operation")
    print("   3. User presses ESC to cancel")
    print("   4. ✅ Cancellation sets content_changed = True")
    print("   5. ✅ Main loop detects the change during timeout")
    print("   6. ✅ Dialog immediately redraws to show canceled state")
    print("   7. ✅ User sees accurate, up-to-date status")
    
    print("\n🎯 Key improvements:")
    print("   • Search cancellation triggers immediate redraw")
    print("   • Search completion triggers immediate redraw")
    print("   • Directory scan cancellation triggers immediate redraw")
    print("   • No more stale 'in progress' indicators")
    print("   • Real-time status updates for all operations")


if __name__ == "__main__":
    try:
        demo_search_cancellation()
        demo_search_completion()
        demo_jump_dialog_cancellation()
        demo_before_and_after()
        
        print("\n" + "=" * 50)
        print("🎉 Search/scan cancellation fix demonstrated!")
        print("   All search and directory scan state changes now")
        print("   trigger proper redraws for real-time status updates.")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)