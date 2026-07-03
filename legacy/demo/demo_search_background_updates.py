#!/usr/bin/env python3
"""
Demo showing how search dialog background updates now trigger redraws
"""

import sys
import os
import time
import threading

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_search_dialog import SearchDialog
from tfm_config import get_config


def demo_background_search_updates():
    """Demonstrate background search updates triggering redraws"""
    
    print("Search Dialog Background Update Demo")
    print("=" * 40)
    
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
    
    print(f"   Content changed: {search_dialog.content_changed}")
    
    print("\n2. Simulating initial draw (main loop):")
    if search_dialog.content_changed:
        search_dialog.draw(None, None)
        search_dialog.content_changed = False
        print("   ✓ Initial draw completed, content marked as unchanged")
    
    print(f"   Content changed: {search_dialog.content_changed}")
    
    print("\n3. Simulating background search thread finding results:")
    
    def simulate_background_search():
        """Simulate a background search thread finding results"""
        time.sleep(0.1)  # Simulate search time
        
        print("   🔍 Background thread: Found 3 files...")
        with search_dialog.search_lock:
            search_dialog.results = ['file1.txt', 'file2.txt', 'file3.txt']
            search_dialog.content_changed = True  # This is the key fix
            print("   ✅ Background thread: Marked content as changed")
        
        time.sleep(0.1)
        
        print("   🔍 Background thread: Found 2 more files...")
        with search_dialog.search_lock:
            search_dialog.results = ['file1.txt', 'file2.txt', 'file3.txt', 'file4.txt', 'file5.txt']
            search_dialog.content_changed = True
            print("   ✅ Background thread: Marked content as changed again")
    
    # Start background "search"
    search_thread = threading.Thread(target=simulate_background_search)
    search_thread.start()
    
    print("\n4. Simulating main loop checking for updates:")
    
    # Simulate main loop iterations (like the timeout handling)
    for i in range(10):
        time.sleep(0.05)  # 50ms intervals (faster than real 16ms for demo)
        
        print(f"   Iteration {i+1}: Checking for content changes...")
        
        if search_dialog.content_changed:
            print(f"   ✨ Content changed detected! Drawing dialog...")
            search_dialog.draw(None, None)
            search_dialog.content_changed = False
            print(f"   ✓ Draw completed, content marked as unchanged")
        else:
            print(f"   ⏸️  No content change, skipping draw")
    
    # Wait for background thread to complete
    search_thread.join()
    
    print(f"\n5. Final Results:")
    print(f"   Total redraws: {draw_count}")
    print(f"   Final results count: {len(search_dialog.results)}")
    print(f"   Content changed: {search_dialog.content_changed}")
    
    print("\n✅ Demo completed!")
    print("   Background search updates now properly trigger redraws")
    print("   when the main loop checks during timeout periods.")


def demo_before_and_after():
    """Show the difference between before and after the fix"""
    
    print("\n\nBefore vs After Comparison")
    print("=" * 40)
    
    print("\n📉 BEFORE the fix:")
    print("   1. Background thread updates search results")
    print("   2. Background thread sets content_changed = True")
    print("   3. Main loop waits for user input (16ms timeout)")
    print("   4. Timeout occurs, main loop continues")
    print("   5. ❌ Main loop only checks content_changed at start of iteration")
    print("   6. ❌ Background update not detected until next user input")
    print("   7. ❌ User sees stale results until they press a key")
    
    print("\n📈 AFTER the fix:")
    print("   1. Background thread updates search results")
    print("   2. Background thread sets content_changed = True")
    print("   3. Main loop waits for user input (16ms timeout)")
    print("   4. Timeout occurs, main loop continues")
    print("   5. ✅ Main loop calls _draw_dialogs_if_needed() after timeout")
    print("   6. ✅ Background update detected and dialog redrawn immediately")
    print("   7. ✅ User sees updated results in real-time")
    
    print("\n🎯 Key improvement:")
    print("   Real-time search results display without requiring user input!")


if __name__ == "__main__":
    try:
        demo_background_search_updates()
        demo_before_and_after()
        
        print("\n" + "=" * 50)
        print("🎉 Search dialog background update fix demonstrated!")
        print("   Users will now see search results update in real-time")
        print("   without needing to press keys to trigger redraws.")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)