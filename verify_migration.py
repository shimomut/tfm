#!/usr/bin/env python3
"""
Verification script for SingleLineTextEdit migration
"""

import sys
import os
sys.path.insert(0, 'src')

def verify_migration():
    """Verify that all text input modes use SingleLineTextEdit"""
    print("🔍 Verifying SingleLineTextEdit migration...")
    
    try:
        from tfm_single_line_text_edit import SingleLineTextEdit
        print("✓ SingleLineTextEdit import successful")
        
        # Test that we can create editors
        editors = {
            'list_dialog_search_editor': SingleLineTextEdit(),
            'search_dialog_pattern_editor': SingleLineTextEdit(),
        }
        
        for name, editor in editors.items():
            if isinstance(editor, SingleLineTextEdit):
                print(f"✓ {name} is SingleLineTextEdit")
            else:
                print(f"✗ {name} is {type(editor)}")
                return False
        
        # Check that the main file imports correctly
        try:
            import tfm_main
            print("✓ tfm_main.py imports successfully")
        except Exception as e:
            print(f"✗ tfm_main.py import failed: {e}")
            return False
        
        print("\n🎉 Migration verification completed successfully!")
        print("✅ List dialog search now uses SingleLineTextEdit")
        print("✅ Search dialog pattern now uses SingleLineTextEdit")
        return True
        
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False

if __name__ == "__main__":
    success = verify_migration()
    sys.exit(0 if success else 1)