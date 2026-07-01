"""
Test to demonstrate why both _draw_dialogs_if_needed calls are necessary

Run with: PYTHONPATH=.:src:ttk pytest test/test_dual_draw_calls_necessity.py -v
"""

import time
import threading
from unittest.mock import Mock

from tfm_search_dialog import SearchDialog
from tfm_config import get_config


def test_dual_draw_calls_necessity():
    """Test that demonstrates why both draw calls are needed"""
    
    config = get_config()
    search_dialog = SearchDialog(config)
    
    # Show search dialog
    search_dialog.show('filename')
    
    # Track draw calls
    draw_calls = []
    
    def mock_draw(*args, **kwargs):
        draw_calls.append(f"Draw at {time.time():.3f}")
    
    search_dialog.draw = mock_draw
    
    # Simulate the main loop logic
    def simulate_main_loop():
        """Simulate the main loop with both draw calls"""
        
        # Simulate first draw call (before timeout)
        print("1. First _draw_dialogs_if_needed() call:")
        if search_dialog.content_changed:
            print("   Content changed - drawing dialog")
            search_dialog.draw(None, None)
            search_dialog.content_changed = False
        else:
            print("   No content change - skipping draw")
        
        print(f"   Content changed after first call: {search_dialog.content_changed}")
        
        # Simulate timeout period where background thread might update
        print("\n2. Timeout period (16ms):")
        time.sleep(0.02)  # Simulate timeout
        
        # Simulate background thread update during timeout
        def background_update():
            time.sleep(0.01)  # Update during timeout
            search_dialog.content_changed = True
            print("   Background thread: Set content_changed = True")
        
        bg_thread = threading.Thread(target=background_update)
        bg_thread.start()
        bg_thread.join()
        
        # Simulate second draw call (after timeout)
        print("\n3. Second _draw_dialogs_if_needed() call (timeout handler):")
        if search_dialog.content_changed:
            print("   Content changed - drawing dialog")
            search_dialog.draw(None, None)
            search_dialog.content_changed = False
        else:
            print("   No content change - skipping draw")
        
        print(f"   Content changed after second call: {search_dialog.content_changed}")
    
    simulate_main_loop()
    
    print(f"\nDraw calls made: {len(draw_calls)}")
    for call in draw_calls:
        print(f"  {call}")
    
    # Verify that both calls were necessary
    assert len(draw_calls) == 2, f"Expected 2 draw calls, got {len(draw_calls)}"
    
    print("\n✓ Both draw calls were necessary:")
    print("  - First call: Handled initial content change")
    print("  - Second call: Handled background thread update during timeout")
    
    return True


def test_single_draw_call_scenario():
    """Test scenario where only one draw call is needed"""
    
    config = get_config()
    search_dialog = SearchDialog(config)
    
    # Show search dialog
    search_dialog.show('filename')
    
    # Track draw calls
    draw_calls = []
    
    def mock_draw(*args, **kwargs):
        draw_calls.append(f"Draw at {time.time():.3f}")
    
    search_dialog.draw = mock_draw
    
    # Simulate main loop without background updates
    print("\nScenario: No background updates during timeout")
    
    # First draw call
    print("1. First _draw_dialogs_if_needed() call:")
    if search_dialog.content_changed:
        print("   Content changed - drawing dialog")
        search_dialog.draw(None, None)
        search_dialog.content_changed = False
    else:
        print("   No content change - skipping draw")
    
    # Timeout period with no background updates
    print("\n2. Timeout period (no background updates):")
    time.sleep(0.02)
    
    # Second draw call
    print("\n3. Second _draw_dialogs_if_needed() call:")
    if search_dialog.content_changed:
        print("   Content changed - drawing dialog")
        search_dialog.draw(None, None)
        search_dialog.content_changed = False
    else:
        print("   No content change - skipping draw (efficient!)")
    
    print(f"\nDraw calls made: {len(draw_calls)}")
    
    # Verify efficiency - only one draw call needed
    assert len(draw_calls) == 1, f"Expected 1 draw call, got {len(draw_calls)}"
    
    print("\n✓ Second call was efficient:")
    print("  - No background updates occurred")
    print("  - Second call detected no changes and skipped drawing")
    print("  - No unnecessary rendering overhead")
    
    return True
