"""
Test to verify NFD/NFC normalization issue in compare_selection feature.

This test creates files with NFD and NFC forms of the same logical filename
to verify if compare_selection properly normalizes before comparing.

Run with: PYTHONPATH=.:src:ttk python temp/test_compare_selection_nfd.py
"""

import sys
import tempfile
import shutil
import unicodedata
from pathlib import Path

from tfm_list_dialog import ListDialogHelpers


class MockListDialog:
    """Mock list dialog for testing"""
    def __init__(self):
        self.title = None
        self.options = None
        self.callback = None
    
    def show(self, title, options, callback):
        self.title = title
        self.options = options
        self.callback = callback


def create_test_structure_with_nfd_nfc():
    """Create test directory structure with NFD and NFC filenames"""
    temp_dir = tempfile.mkdtemp(prefix="tfm_nfd_test_")
    left_dir = Path(temp_dir) / "left"
    right_dir = Path(temp_dir) / "right"
    
    left_dir.mkdir()
    right_dir.mkdir()
    
    # Create files with NFD form in left pane (as macOS would)
    nfd_filename = unicodedata.normalize('NFD', "テストファイル_が.txt")
    (left_dir / nfd_filename).write_text("content")
    
    # Create files with NFC form in right pane (as Linux/Windows would)
    nfc_filename = unicodedata.normalize('NFC', "テストファイル_が.txt")
    (right_dir / nfc_filename).write_text("content")
    
    print(f"Created NFD file: {repr(nfd_filename)}")
    print(f"Created NFC file: {repr(nfc_filename)}")
    print(f"Are they equal? {nfd_filename == nfc_filename}")
    print(f"NFD bytes: {nfd_filename.encode('utf-8')}")
    print(f"NFC bytes: {nfc_filename.encode('utf-8')}")
    
    return temp_dir, left_dir, right_dir


def create_pane_data(directory):
    """Create pane data structure for testing"""
    files = list(directory.iterdir())
    return {
        'path': directory,
        'files': files,
        'selected_files': set(),
        'selected_index': 0
    }


def test_nfd_nfc_comparison():
    """Test that NFD and NFC forms of same filename are matched"""
    print("\n" + "="*70)
    print("Testing NFD/NFC normalization in compare_selection...")
    print("="*70)
    
    temp_dir, left_dir, right_dir = create_test_structure_with_nfd_nfc()
    
    try:
        # Create pane data
        current_pane = create_pane_data(left_dir)
        other_pane = create_pane_data(right_dir)
        
        print(f"\nLeft pane files: {[f.name for f in current_pane['files']]}")
        print(f"Right pane files: {[f.name for f in other_pane['files']]}")
        
        # Create mock dialog
        mock_dialog = MockListDialog()
        
        # Track print messages
        messages = []
        def mock_print(msg):
            messages.append(msg)
            print(f"  {msg}")
        
        # Test the compare selection functionality
        ListDialogHelpers.show_compare_selection(
            mock_dialog, current_pane, other_pane, mock_print
        )
        
        # Test "By filename" comparison
        print("\nTesting 'By filename' comparison with NFD/NFC...")
        messages.clear()
        current_pane['selected_files'].clear()
        
        mock_dialog.callback("By filename")
        
        # Check if the NFD file was selected (should match NFC file)
        selected_items = current_pane['selected_files']
        print(f"\nSelected items: {selected_items}")
        print(f"Number of selected items: {len(selected_items)}")
        
        if len(selected_items) == 1:
            print("\n✅ SUCCESS: NFD and NFC forms were matched!")
            print("The compare_selection feature correctly normalizes filenames.")
        else:
            print("\n❌ FAILURE: NFD and NFC forms were NOT matched!")
            print("The compare_selection feature needs to normalize filenames before comparing.")
            print("\nExpected: 1 file selected (NFD file matching NFC file)")
            print(f"Actual: {len(selected_items)} files selected")
            
            # Show the messages
            print("\nMessages:")
            for msg in messages:
                print(f"  {msg}")
        
        return len(selected_items) == 1
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    success = test_nfd_nfc_comparison()
    sys.exit(0 if success else 1)
