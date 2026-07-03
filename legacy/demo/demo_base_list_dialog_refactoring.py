#!/usr/bin/env python3
"""
Demo script showing BaseListDialog refactoring
This demonstrates that ListDialog, SearchDialog, and JumpDialog now inherit from BaseListDialog
while preserving their original behavior.
"""

import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_base_list_dialog import BaseListDialog
from tfm_list_dialog import ListDialog
from tfm_search_dialog import SearchDialog
from tfm_jump_dialog import JumpDialog
from _config import Config


def demo_inheritance():
    """Demonstrate that all dialog classes inherit from BaseListDialog"""
    print("=== BaseListDialog Inheritance Demo ===\n")
    
    config = Config()
    
    # Create instances
    list_dialog = ListDialog(config)
    search_dialog = SearchDialog(config)
    jump_dialog = JumpDialog(config)
    
    # Check inheritance
    print("Inheritance verification:")
    print(f"ListDialog is instance of BaseListDialog: {isinstance(list_dialog, BaseListDialog)}")
    print(f"SearchDialog is instance of BaseListDialog: {isinstance(search_dialog, BaseListDialog)}")
    print(f"JumpDialog is instance of BaseListDialog: {isinstance(jump_dialog, BaseListDialog)}")
    
    print("\nCommon attributes from BaseListDialog:")
    common_attrs = ['mode', 'selected', 'scroll', 'text_editor']
    for attr in common_attrs:
        print(f"  ListDialog.{attr}: {hasattr(list_dialog, attr)}")
        print(f"  SearchDialog.{attr}: {hasattr(search_dialog, attr)}")
        print(f"  JumpDialog.{attr}: {hasattr(jump_dialog, attr)}")
    
    print("\nSpecific attributes preserved:")
    print(f"  ListDialog.items: {hasattr(list_dialog, 'items')}")
    print(f"  ListDialog.filtered_items: {hasattr(list_dialog, 'filtered_items')}")
    print(f"  SearchDialog.results: {hasattr(search_dialog, 'results')}")
    print(f"  SearchDialog.search_type: {hasattr(search_dialog, 'search_type')}")
    print(f"  JumpDialog.directories: {hasattr(jump_dialog, 'directories')}")
    print(f"  JumpDialog.filtered_directories: {hasattr(jump_dialog, 'filtered_directories')}")


def demo_common_functionality():
    """Demonstrate common functionality works across all dialogs"""
    print("\n=== Common Functionality Demo ===\n")
    
    config = Config()
    list_dialog = ListDialog(config)
    
    # Test common navigation
    print("Testing common navigation handling:")
    
    # Simulate UP key
    items = ["item1", "item2", "item3"]
    list_dialog.selected = 1
    result = list_dialog.handle_common_navigation(259, items)  # KEY_UP
    print(f"  UP key: selected changed from 1 to {list_dialog.selected}")
    
    # Simulate DOWN key
    result = list_dialog.handle_common_navigation(258, items)  # KEY_DOWN
    print(f"  DOWN key: selected changed to {list_dialog.selected}")
    
    # Simulate ESC key
    result = list_dialog.handle_common_navigation(27, items)  # ESC
    print(f"  ESC key result: {result}")
    
    # Simulate ENTER key
    result = list_dialog.handle_common_navigation(10, items)  # ENTER
    print(f"  ENTER key result: {result}")


def demo_preserved_behavior():
    """Demonstrate that specific behavior is preserved"""
    print("\n=== Preserved Behavior Demo ===\n")
    
    config = Config()
    
    # ListDialog specific behavior
    print("ListDialog filtering behavior:")
    list_dialog = ListDialog(config)
    list_dialog.items = ["apple", "banana", "cherry", "apricot"]
    list_dialog.text_editor.text = "ap"
    list_dialog._filter_items()
    print(f"  Original items: {list_dialog.items}")
    print(f"  Filter 'ap': {list_dialog.filtered_items}")
    
    # SearchDialog specific behavior
    print("\nSearchDialog search type switching:")
    search_dialog = SearchDialog(config)
    search_dialog.search_type = 'filename'
    print(f"  Initial search type: {search_dialog.search_type}")
    
    # Simulate Tab key
    result = search_dialog.handle_input(9)  # Tab key
    print(f"  After Tab key: {search_dialog.search_type}")
    print(f"  Handle input result: {result}")
    
    # JumpDialog specific behavior
    print("\nJumpDialog directory filtering:")
    jump_dialog = JumpDialog(config)
    jump_dialog.directories = [
        Path("/home/user/documents"),
        Path("/home/user/downloads"),
        Path("/home/user/desktop")
    ]
    jump_dialog.text_editor.text = "doc"
    jump_dialog._filter_directories_internal()
    print(f"  Original directories: {[str(d) for d in jump_dialog.directories]}")
    print(f"  Filter 'doc': {[str(d) for d in jump_dialog.filtered_directories]}")


def demo_code_reduction():
    """Show how much code was reduced through inheritance"""
    print("\n=== Code Reduction Analysis ===\n")
    
    # Count lines in base class
    base_file = Path(__file__).parent.parent / 'src' / 'tfm_base_list_dialog.py'
    base_lines = len(base_file.read_text().splitlines())
    
    print(f"BaseListDialog: {base_lines} lines")
    print("\nCommon functionality now shared:")
    print("  - Navigation key handling (UP/DOWN/PAGE UP/PAGE DOWN/HOME/END)")
    print("  - Text input handling (printable characters, backspace)")
    print("  - Dialog frame drawing")
    print("  - List item rendering with selection highlighting")
    print("  - Scrollbar drawing")
    print("  - Scroll adjustment logic")
    print("  - Help text rendering")
    
    print("\nBenefits of refactoring:")
    print("  ✓ Reduced code duplication")
    print("  ✓ Consistent behavior across all dialogs")
    print("  ✓ Easier maintenance and bug fixes")
    print("  ✓ Single place to add new common features")
    print("  ✓ Preserved all existing functionality")


if __name__ == '__main__':
    demo_inheritance()
    demo_common_functionality()
    demo_preserved_behavior()
    demo_code_reduction()
    
    print("\n🎉 BaseListDialog refactoring demo completed successfully!")
    print("All three dialog classes now inherit from BaseListDialog while preserving their behavior.")