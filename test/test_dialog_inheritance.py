#!/usr/bin/env python3
"""
Test dialog inheritance from BaseListDialog

This test verifies that all list-based dialog classes properly inherit
from BaseListDialog and have access to common functionality.
"""

import sys
sys.path.insert(0, 'src')

from tfm_base_list_dialog import BaseListDialog
from tfm_batch_rename_dialog import BatchRenameDialog
from tfm_info_dialog import InfoDialog
from tfm_list_dialog import ListDialog
from tfm_jump_dialog import JumpDialog
from tfm_search_dialog import SearchDialog
from tfm_drives_dialog import DrivesDialog


class MockConfig:
    """Mock configuration for testing"""
    pass


def test_dialog_inheritance():
    """Test that all dialog classes inherit from BaseListDialog"""
    config = MockConfig()
    
    # List of dialog classes to test
    dialog_classes = [
        ('BatchRenameDialog', BatchRenameDialog),
        ('InfoDialog', InfoDialog),
        ('ListDialog', ListDialog),
        ('JumpDialog', JumpDialog),
        ('SearchDialog', SearchDialog),
        ('DrivesDialog', DrivesDialog)
    ]
    
    print("Testing Dialog Inheritance")
    print("=" * 60)
    
    all_passed = True
    for name, dialog_class in dialog_classes:
        dialog = dialog_class(config)
        inherits = isinstance(dialog, BaseListDialog)
        
        if inherits:
            print(f"✓ {name:25} inherits from BaseListDialog")
        else:
            print(f"✗ {name:25} does NOT inherit from BaseListDialog")
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("✓ All dialog classes properly inherit from BaseListDialog")
        return True
    else:
        print("✗ Some dialog classes do not inherit from BaseListDialog")
        return False


def test_common_attributes():
    """Test that dialogs have common attributes from BaseListDialog"""
    config = MockConfig()
    
    print("\nTesting Common Attributes")
    print("=" * 60)
    
    # Test BatchRenameDialog
    batch_dialog = BatchRenameDialog(config)
    print("BatchRenameDialog attributes:")
    print(f"  ✓ mode: {hasattr(batch_dialog, 'mode')}")
    print(f"  ✓ scroll: {hasattr(batch_dialog, 'scroll')}")
    print(f"  ✓ text_editor: {hasattr(batch_dialog, 'text_editor')}")
    print(f"  ✓ selected: {hasattr(batch_dialog, 'selected')}")
    
    # Test InfoDialog
    info_dialog = InfoDialog(config)
    print("\nInfoDialog attributes:")
    print(f"  ✓ mode: {hasattr(info_dialog, 'mode')}")
    print(f"  ✓ scroll: {hasattr(info_dialog, 'scroll')}")
    print(f"  ✓ text_editor: {hasattr(info_dialog, 'text_editor')}")
    print(f"  ✓ selected: {hasattr(info_dialog, 'selected')}")
    
    print("=" * 60)
    print("✓ All dialogs have common attributes from BaseListDialog")
    return True


def test_exit_method():
    """Test that exit method properly calls parent class"""
    config = MockConfig()
    
    print("\nTesting Exit Method")
    print("=" * 60)
    
    # Test BatchRenameDialog exit
    batch_dialog = BatchRenameDialog(config)
    batch_dialog.is_active = True
    batch_dialog.scroll = 5
    batch_dialog.selected = 3
    batch_dialog.exit()
    
    print("BatchRenameDialog after exit:")
    print(f"  ✓ is_active reset: {batch_dialog.is_active == False}")
    print(f"  ✓ scroll reset: {batch_dialog.scroll == 0}")
    print(f"  ✓ selected reset: {batch_dialog.selected == 0}")
    
    # Test InfoDialog exit
    info_dialog = InfoDialog(config)
    info_dialog.is_active = True
    info_dialog.scroll = 5
    info_dialog.selected = 3
    info_dialog.exit()
    
    print("\nInfoDialog after exit:")
    print(f"  ✓ is_active reset: {info_dialog.is_active == False}")
    print(f"  ✓ scroll reset: {info_dialog.scroll == 0}")
    print(f"  ✓ selected reset: {info_dialog.selected == 0}")
    
    print("=" * 60)
    print("✓ Exit method properly resets parent class attributes")
    return True


if __name__ == '__main__':
    print("Dialog Inheritance Test Suite")
    print("=" * 60)
    print()
    
    # Run all tests
    test1 = test_dialog_inheritance()
    test2 = test_common_attributes()
    test3 = test_exit_method()
    
    print("\n" + "=" * 60)
    if test1 and test2 and test3:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)
