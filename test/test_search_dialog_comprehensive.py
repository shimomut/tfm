"""
Comprehensive test for SearchDialog thread-safe content_changed handling

Run with: PYTHONPATH=.:src:ttk pytest test/test_search_dialog_comprehensive.py -v
"""

import time
import threading
from unittest.mock import Mock, patch

from tfm_search_dialog import SearchDialog
from tfm_config import get_config


def test_comprehensive_search_dialog():
    """Test SearchDialog with simulated main loop and background search"""
    
    config = get_config()
    search_dialog = SearchDialog(config)
    
    # Show the search dialog
    search_dialog.show('filename')
    search_dialog.text_editor.set_text('test')
    
    # Track events
    events = []
    draw_count = 0
    
    def mock_draw(*args, **kwargs):
        nonlocal draw_count
        draw_count += 1
        events.append(f'DRAW: Dialog drawn (#{draw_count})')
    
    search_dialog.draw = mock_draw
    
    # Simulate main loop methods with thread-safe access
    def check_content_changed():
        with search_dialog.search_lock:
            return search_dialog.content_changed
    
    def mark_content_unchanged():
        with search_dialog.search_lock:
            search_dialog.content_changed = False
    
    # Simulate background search finding results
    def background_search():
        """Simulate background search thread"""
        temp_results = []
        
        for i in range(5):
            time.sleep(0.02)  # Simulate search time
            
            # Add some results
            for j in range(10):
                temp_results.append(f'file_{i}_{j}.txt')
            
            # Update results (this is what the real search thread does)
            with search_dialog.search_lock:
                search_dialog.results = temp_results.copy()
                search_dialog.content_changed = True
                events.append(f'BG: Found {len(temp_results)} results, marked content_changed=True')
    
    # Simulate main loop
    def main_loop():
        """Simulate main loop checking for updates"""
        for iteration in range(20):
            time.sleep(0.01)  # 10ms intervals
            
            # Check for content changes (thread-safe)
            if check_content_changed():
                events.append(f'MAIN: Detected content change (iteration {iteration})')
                
                # Draw dialog
                search_dialog.draw(None, None)
                
                # Mark as unchanged
                mark_content_unchanged()
                events.append(f'MAIN: Marked content unchanged (iteration {iteration})')
            else:
                events.append(f'MAIN: No content change (iteration {iteration})')
    
    # Start background search
    bg_thread = threading.Thread(target=background_search)
    main_thread = threading.Thread(target=main_loop)
    
    bg_thread.start()
    main_thread.start()
    
    # Wait for completion
    bg_thread.join()
    main_thread.join()
    
    # Analyze results
    print("Event sequence:")
    for event in events:
        print(f"  {event}")
    
    print(f"\nSummary:")
    print(f"  Total draws: {draw_count}")
    print(f"  Final results count: {len(search_dialog.results)}")
    
    # Verify results
    bg_updates = len([e for e in events if 'BG: Found' in e])
    main_detections = len([e for e in events if 'MAIN: Detected content change' in e])
    
    assert bg_updates > 0, "Background thread should have made updates"
    assert main_detections > 0, "Main thread should have detected updates"
    assert draw_count > 0, "Dialog should have been drawn"
    assert len(search_dialog.results) == 50, "Should have found 50 results total"
    
    print("✓ Comprehensive SearchDialog test passed")
    return True


def test_user_interaction_during_search():
    """Test user interactions while background search is running"""
    
    config = get_config()
    search_dialog = SearchDialog(config)
    
    # Show the search dialog
    search_dialog.show('filename')
    
    events = []
    
    # Simulate background search
    def background_search():
        for i in range(3):
            time.sleep(0.05)
            with search_dialog.search_lock:
                search_dialog.results.append(f'bg_file_{i}.txt')
                search_dialog.content_changed = True
                events.append(f'BG: Added result {i}')
    
    # Simulate user interactions
    def user_interactions():
        time.sleep(0.02)
        
        # User switches search type
        search_dialog.handle_input(ord('\t'))  # Tab key
        events.append('USER: Switched search type')
        
        time.sleep(0.03)
        
        # User navigates (simulate down arrow)
        from ttk import KeyEvent, KeyCode, ModifierKey
        search_dialog.handle_input(KeyEvent(key_code=KeyCode.DOWN, modifiers=ModifierKey.NONE))
        events.append('USER: Navigated down')
        
        time.sleep(0.03)
        
        # User types (simulate text change)
        search_dialog.handle_input(ord('a'))
        events.append('USER: Typed character')
    
    # Start both threads
    bg_thread = threading.Thread(target=background_search)
    user_thread = threading.Thread(target=user_interactions)
    
    bg_thread.start()
    user_thread.start()
    
    # Simulate main loop checking
    for i in range(10):
        time.sleep(0.02)
        
        with search_dialog.search_lock:
            changed = search_dialog.content_changed
        
        if changed:
            events.append(f'MAIN: Detected change (iteration {i})')
            with search_dialog.search_lock:
                search_dialog.content_changed = False
    
    bg_thread.join()
    user_thread.join()
    
    print("\nUser interaction test events:")
    for event in events:
        print(f"  {event}")
    
    # Verify that both background and user events were detected
    bg_events = len([e for e in events if 'BG:' in e])
    user_events = len([e for e in events if 'USER:' in e])
    main_detections = len([e for e in events if 'MAIN: Detected' in e])
    
    assert bg_events > 0, "Should have background events"
    assert user_events > 0, "Should have user events"
    assert main_detections > 0, "Should have detected changes"
    
    print("✓ User interaction during search test passed")
    return True
