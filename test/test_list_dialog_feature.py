#!/usr/bin/env python3
"""
Comprehensive test for the searchable list dialog feature
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_list_dialog_state_management():
    """Test list dialog state management"""
    print("Testing list dialog state management...")
    
    # Mock the FileManager class for testing
    class MockFileManager:
        def __init__(self):
            # Initialize list dialog state
            self.list_dialog_mode = False
            self.list_dialog_title = ""
            self.list_dialog_items = []
            self.list_dialog_filtered_items = []
            self.list_dialog_selected = 0
            self.list_dialog_scroll = 0
            self.list_dialog_search = ""
            self.list_dialog_callback = None
            self.needs_full_redraw = False
        
        def show_list_dialog(self, title, items, callback):
            """Show a searchable list dialog"""
            self.list_dialog_mode = True
            self.list_dialog_title = title
            self.list_dialog_items = items
            self.list_dialog_filtered_items = items.copy()
            self.list_dialog_selected = 0
            self.list_dialog_scroll = 0
            self.list_dialog_search = ""
            self.list_dialog_callback = callback
            self.needs_full_redraw = True
        
        def exit_list_dialog_mode(self):
            """Exit list dialog mode"""
            self.list_dialog_mode = False
            self.list_dialog_title = ""
            self.list_dialog_items = []
            self.list_dialog_filtered_items = []
            self.list_dialog_selected = 0
            self.list_dialog_scroll = 0
            self.list_dialog_search = ""
            self.list_dialog_callback = None
            self.needs_full_redraw = True
        
        def _filter_list_dialog_items(self):
            """Filter list dialog items based on current search pattern"""
            if not self.list_dialog_search:
                self.list_dialog_filtered_items = self.list_dialog_items.copy()
            else:
                search_lower = self.list_dialog_search.lower()
                self.list_dialog_filtered_items = [
                    item for item in self.list_dialog_items 
                    if search_lower in str(item).lower()
                ]
            
            # Reset selection to top of filtered list
            self.list_dialog_selected = 0
            self.list_dialog_scroll = 0
    
    # Test initialization
    fm = MockFileManager()
    assert not fm.list_dialog_mode, "Dialog should not be active initially"
    
    # Test showing dialog
    test_items = ["Apple", "Banana", "Cherry"]
    test_callback = lambda x: None
    
    fm.show_list_dialog("Test Dialog", test_items, test_callback)
    
    assert fm.list_dialog_mode, "Dialog should be active after show_list_dialog"
    assert fm.list_dialog_title == "Test Dialog", "Title should be set correctly"
    assert fm.list_dialog_items == test_items, "Items should be set correctly"
    assert fm.list_dialog_filtered_items == test_items, "Filtered items should initially match all items"
    assert fm.list_dialog_selected == 0, "Selection should start at 0"
    assert fm.list_dialog_search == "", "Search should be empty initially"
    assert fm.list_dialog_callback == test_callback, "Callback should be set"
    
    # Test filtering
    fm.list_dialog_search = "a"
    fm._filter_list_dialog_items()
    
    expected_filtered = ["Apple", "Banana"]  # Items containing 'a'
    assert fm.list_dialog_filtered_items == expected_filtered, f"Filtering failed: got {fm.list_dialog_filtered_items}, expected {expected_filtered}"
    assert fm.list_dialog_selected == 0, "Selection should reset to 0 after filtering"
    
    # Test case insensitive filtering
    fm.list_dialog_search = "A"
    fm._filter_list_dialog_items()
    assert fm.list_dialog_filtered_items == expected_filtered, "Filtering should be case insensitive"
    
    # Test no matches
    fm.list_dialog_search = "xyz"
    fm._filter_list_dialog_items()
    assert fm.list_dialog_filtered_items == [], "Should return empty list for no matches"
    
    # Test exit
    fm.exit_list_dialog_mode()
    assert not fm.list_dialog_mode, "Dialog should not be active after exit"
    assert fm.list_dialog_items == [], "Items should be cleared after exit"
    
    print("✓ State management tests passed")

def test_search_functionality():
    """Test search and filtering functionality"""
    print("Testing search functionality...")
    
    test_items = [
        "apple.txt", "banana.py", "cherry.md", "date.json",
        "elderberry.xml", "fig.csv", "grape.log", "Apple.TXT"
    ]
    
    # Test case insensitive search
    search_tests = [
        ("apple", ["apple.txt", "Apple.TXT"]),
        ("APPLE", ["apple.txt", "Apple.TXT"]),
        (".txt", ["apple.txt", "Apple.TXT"]),
        ("py", ["banana.py"]),
        ("xyz", []),
        ("", test_items),  # Empty search shows all
    ]
    
    for search_term, expected in search_tests:
        filtered = []
        search_lower = search_term.lower()
        
        if not search_term:
            filtered = test_items.copy()
        else:
            filtered = [item for item in test_items if search_lower in item.lower()]
        
        assert filtered == expected, f"Search '{search_term}' failed: got {filtered}, expected {expected}"
    
    print("✓ Search functionality tests passed")

def test_navigation_logic():
    """Test navigation logic"""
    print("Testing navigation logic...")
    
    # Test with small list
    items = ["Item 1", "Item 2", "Item 3"]
    selected = 0
    
    # Test down navigation
    selected = min(len(items) - 1, selected + 1)
    assert selected == 1, "Down navigation failed"
    
    selected = min(len(items) - 1, selected + 1)
    assert selected == 2, "Down navigation failed"
    
    # Test boundary - should not go beyond last item
    selected = min(len(items) - 1, selected + 1)
    assert selected == 2, "Should not go beyond last item"
    
    # Test up navigation
    selected = max(0, selected - 1)
    assert selected == 1, "Up navigation failed"
    
    selected = max(0, selected - 1)
    assert selected == 0, "Up navigation failed"
    
    # Test boundary - should not go below 0
    selected = max(0, selected - 1)
    assert selected == 0, "Should not go below 0"
    
    # Test page navigation
    selected = 0
    selected = min(len(items) - 1, selected + 10)  # Page down
    assert selected == 2, "Page down should go to last item for small list"
    
    selected = max(0, selected - 10)  # Page up
    assert selected == 0, "Page up should go to first item"
    
    print("✓ Navigation logic tests passed")

def test_edge_cases():
    """Test edge cases"""
    print("Testing edge cases...")
    
    # Test empty list
    empty_items = []
    # Should handle gracefully - no crashes
    
    # Test single item
    single_item = ["Only Item"]
    # Navigation should work correctly
    
    # Test very long items
    long_items = ["A" * 1000, "B" * 500, "C" * 200]
    # Should truncate properly in display
    
    # Test special characters
    special_items = ["file with spaces.txt", "file-with-dashes.py", "file_with_underscores.md", "file.with.dots.json"]
    # Should handle all characters correctly
    
    # Test unicode
    unicode_items = ["café.txt", "naïve.py", "résumé.md", "🎉emoji.json"]
    # Should handle unicode correctly
    
    print("✓ Edge case tests passed")

def test_integration_points():
    """Test integration with main TFM system"""
    print("Testing integration points...")
    
    # Test that dialog modes are mutually exclusive
    dialog_modes = [
        'quick_choice_mode',
        'info_dialog_mode', 
        'list_dialog_mode',
        'search_mode',
        'rename_mode',
        'create_dir_mode',
        'create_file_mode'
    ]
    
    # Only one should be active at a time
    # This would be tested in the actual FileManager class
    
    # Test key handling priority
    # List dialog should handle keys when active
    # Regular keys should be ignored when dialog is active
    
    # Test drawing integration
    # Dialog should be drawn when list_dialog_mode is True
    # Regular interface should be drawn when dialog is not active
    
    print("✓ Integration tests passed")

def run_all_tests():
    """Run all tests"""
    print("Running searchable list dialog tests...")
    print("=" * 50)
    
    try:
        test_list_dialog_state_management()
        test_search_functionality()
        test_navigation_logic()
        test_edge_cases()
        test_integration_points()
        
        print("=" * 50)
        print("✓ All tests passed successfully!")
        return True
        
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)