"""
Test script for the sort toggle functionality

Run with: PYTHONPATH=.:src:ttk pytest test/test_sort_toggle.py -v
"""

from tfm_main import FileManager
import curses
from ttk import KeyEvent, KeyCode, ModifierKey

def test_sort_toggle():
    """Test the sort toggle functionality without curses"""
    
    # Create a mock pane data structure
    test_pane = {
        'path': Path('.'),
        'selected_index': 0,
        'scroll_offset': 0,
        'files': [],
        'selected_files': set(),
        'sort_mode': 'name',
        'sort_reverse': False
    }
    
    # Create a minimal FileManager-like object for testing
    class MockFileManager:
        def __init__(self):
            self.left_pane = test_pane
            self.right_pane = test_pane.copy()
            self.active_pane = 'left'
            self.needs_full_redraw = False
            
        def get_current_pane(self):
            return self.left_pane if self.active_pane == 'left' else self.right_pane
            
        def refresh_files(self, pane):
            # Mock refresh - just print what would happen
            print(f"  [Mock] Refreshing files for pane with sort_mode={pane['sort_mode']}, sort_reverse={pane['sort_reverse']}")
            
        def quick_sort(self, sort_mode):
            """Quickly change sort mode without showing dialog, or toggle reverse if already sorted by this mode"""
            current_pane = self.get_current_pane()
            pane_name = "left" if self.active_pane == 'left' else "right"
            
            # Check if we're already sorting by this mode
            if current_pane['sort_mode'] == sort_mode:
                # Toggle reverse mode
                current_pane['sort_reverse'] = not current_pane['sort_reverse']
                reverse_status = "reverse" if current_pane['sort_reverse'] else "normal"
                print(f"Toggled {pane_name} pane to {sort_mode} sorting ({reverse_status})")
            else:
                # Change to new sort mode (keep current reverse setting)
                current_pane['sort_mode'] = sort_mode
                print(f"Sorted {pane_name} pane by {sort_mode}")
            
            # Refresh the file list
            self.refresh_files(current_pane)
            self.needs_full_redraw = True
    
    # Test the functionality
    fm = MockFileManager()
    
    print("=== Testing Sort Toggle Functionality ===")
    print(f"Initial state: sort_mode={fm.left_pane['sort_mode']}, sort_reverse={fm.left_pane['sort_reverse']}")
    print()
    
    print("1. Press '1' (name sort) - should keep name sort, no change:")
    fm.quick_sort('name')
    print(f"   Result: sort_mode={fm.left_pane['sort_mode']}, sort_reverse={fm.left_pane['sort_reverse']}")
    print()
    
    print("2. Press '1' again - should toggle reverse:")
    fm.quick_sort('name')
    print(f"   Result: sort_mode={fm.left_pane['sort_mode']}, sort_reverse={fm.left_pane['sort_reverse']}")
    print()
    
    print("3. Press '1' again - should toggle reverse back:")
    fm.quick_sort('name')
    print(f"   Result: sort_mode={fm.left_pane['sort_mode']}, sort_reverse={fm.left_pane['sort_reverse']}")
    print()
    
    print("4. Press '2' (size sort) - should change to size sort:")
    fm.quick_sort('size')
    print(f"   Result: sort_mode={fm.left_pane['sort_mode']}, sort_reverse={fm.left_pane['sort_reverse']}")
    print()
    
    print("5. Press '2' again - should toggle reverse for size:")
    fm.quick_sort('size')
    print(f"   Result: sort_mode={fm.left_pane['sort_mode']}, sort_reverse={fm.left_pane['sort_reverse']}")
    print()
    
    print("6. Press '3' (date sort) - should change to date sort:")
    fm.quick_sort('date')
    print(f"   Result: sort_mode={fm.left_pane['sort_mode']}, sort_reverse={fm.left_pane['sort_reverse']}")
    print()
    
    print("7. Press '3' again - should toggle reverse for date:")
    fm.quick_sort('date')
    print(f"   Result: sort_mode={fm.left_pane['sort_mode']}, sort_reverse={fm.left_pane['sort_reverse']}")
    print()
    
    print("8. Press '1' (back to name) - should change to name sort, keep reverse setting:")
    fm.quick_sort('name')
    print(f"   Result: sort_mode={fm.left_pane['sort_mode']}, sort_reverse={fm.left_pane['sort_reverse']}")
    print()
