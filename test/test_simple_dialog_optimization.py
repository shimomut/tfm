#!/usr/bin/env python3
"""
Simple test to verify dialog content change tracking
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from tfm_general_purpose_dialog import GeneralPurposeDialog
    from tfm_list_dialog import ListDialog
    from tfm_info_dialog import InfoDialog
    from tfm_config import get_config
    
    print("Testing dialog content change tracking...")
    
    config = get_config()
    
    # Test GeneralPurposeDialog
    print("Testing GeneralPurposeDialog...")
    general_dialog = GeneralPurposeDialog(config)
    assert hasattr(general_dialog, 'content_changed'), "GeneralPurposeDialog should have content_changed attribute"
    assert general_dialog.content_changed == True, "content_changed should be True by default"
    
    general_dialog.show_status_line_input("Test prompt")
    assert general_dialog.content_changed == True, "content_changed should be True after showing"
    
    general_dialog.content_changed = False
    general_dialog.handle_key(ord('a'))
    assert general_dialog.content_changed == True, "content_changed should be True after text input"
    
    print("✓ GeneralPurposeDialog content change tracking works")
    
    # Test ListDialog
    print("Testing ListDialog...")
    list_dialog = ListDialog(config)
    assert hasattr(list_dialog, 'content_changed'), "ListDialog should have content_changed attribute"
    
    list_dialog.show("Test", ["item1", "item2"], None)
    assert list_dialog.content_changed == True, "content_changed should be True after showing"
    
    print("✓ ListDialog content change tracking works")
    
    # Test InfoDialog
    print("Testing InfoDialog...")
    info_dialog = InfoDialog(config)
    assert hasattr(info_dialog, 'content_changed'), "InfoDialog should have content_changed attribute"
    
    info_dialog.show("Test", ["line1", "line2"])
    assert info_dialog.content_changed == True, "content_changed should be True after showing"
    
    print("✓ InfoDialog content change tracking works")
    
    print("\n🎉 All basic dialog content change tracking tests passed!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)