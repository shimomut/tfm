"""
Test script to verify Compare & Select feature works with both files and directories.
This test creates a temporary directory structure and verifies the compare selection
functionality handles both files and directories correctly.

Run with: PYTHONPATH=.:src:ttk pytest test/test_compare_selection_directories.py -v
"""

import sys
import tempfile
import shutil
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


def create_test_structure():
    """Create test directory structure with files and directories"""
    # Create temporary directories
    temp_dir = tempfile.mkdtemp(prefix="tfm_test_")
    left_dir = Path(temp_dir) / "left"
    right_dir = Path(temp_dir) / "right"
    
    left_dir.mkdir()
    right_dir.mkdir()
    
    # Create files and directories in left pane
    (left_dir / "file1.txt").write_text("content1")
    (left_dir / "file2.txt").write_text("content2")
    (left_dir / "dir1").mkdir()
    (left_dir / "dir2").mkdir()
    (left_dir / "unique_file.txt").write_text("unique")
    
    # Create matching and non-matching items in right pane
    (right_dir / "file1.txt").write_text("content1")  # Same name, same content
    (right_dir / "file2.txt").write_text("different")  # Same name, different content
    (right_dir / "dir1").mkdir()  # Same directory name
    (right_dir / "dir3").mkdir()  # Different directory name
    (right_dir / "other_file.txt").write_text("other")
    
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


def test_compare_selection_with_directories():
    """Test compare selection functionality with files and directories"""
    print("Testing Compare & Select feature with files and directories...")
    
    temp_dir, left_dir, right_dir = create_test_structure()
    
    try:
        # Create pane data
        current_pane = create_pane_data(left_dir)
        other_pane = create_pane_data(right_dir)
        
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
        
        # Verify dialog was set up correctly
        assert mock_dialog.title == "Compare Selection"
        assert len(mock_dialog.options) == 3
        assert "By filename" in mock_dialog.options
        assert "By filename and size" in mock_dialog.options
        assert "By filename, size, and timestamp" in mock_dialog.options
        
        print("✓ Dialog options set up correctly")
        
        # Test "By filename" comparison
        print("\nTesting 'By filename' comparison...")
        messages.clear()
        current_pane['selected_files'].clear()
        
        mock_dialog.callback("By filename")
        
        # Should select file1.txt, file2.txt, and dir1 (matching names)
        selected_items = current_pane['selected_files']
        print(f"  Selected items: {selected_items}")
        
        # Verify correct items were selected
        selected_names = {Path(item).name for item in selected_items}
        expected_names = {"file1.txt", "file2.txt", "dir1"}
        
        assert selected_names == expected_names, f"Expected {expected_names}, got {selected_names}"
        print("✓ Correct items selected by filename")
        
        # Verify message indicates both files and directories
        success_message = next((msg for msg in messages if "Selected" in msg and "items" in msg), None)
        assert success_message is not None, "No success message found"
        assert "files and" in success_message and "directories" in success_message, f"Message doesn't mention both types: {success_message}"
        print("✓ Success message correctly mentions both files and directories")
        
        # Test with no matches
        print("\nTesting with no matching items...")
        messages.clear()
        current_pane['selected_files'].clear()
        
        # Remove all items from other pane to test no matches
        other_pane['files'] = []
        mock_dialog.callback("By filename")
        
        # Should have no selections and appropriate message
        assert len(current_pane['selected_files']) == 0
        no_items_message = next((msg for msg in messages if "No items" in msg), None)
        assert no_items_message is not None, "No 'no items' message found"
        print("✓ Correctly handles case with no matching items")
        
        print("\n✅ All tests passed! Compare & Select now works with both files and directories.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        shutil.rmtree(temp_dir)
    
    return True


def test_type_mismatch_handling():
    """Test that files and directories with same name don't match each other"""
    print("\nTesting type mismatch handling (file vs directory with same name)...")
    
    temp_dir, left_dir, right_dir = create_test_structure()
    
    try:
        # Create a file in left and directory with same name in right
        (left_dir / "samename").write_text("file content")
        (right_dir / "samename").mkdir()
        
        current_pane = create_pane_data(left_dir)
        other_pane = create_pane_data(right_dir)
        
        mock_dialog = MockListDialog()
        messages = []
        def mock_print(msg):
            messages.append(msg)
            print(f"  {msg}")
        
        ListDialogHelpers.show_compare_selection(
            mock_dialog, current_pane, other_pane, mock_print
        )
        
        # Test comparison - should not match file with directory of same name
        current_pane['selected_files'].clear()
        mock_dialog.callback("By filename")
        
        # "samename" should not be selected because it's a file in left but directory in right
        selected_names = {Path(item).name for item in current_pane['selected_files']}
        assert "samename" not in selected_names, "File and directory with same name should not match"
        
        print("✓ Correctly handles type mismatch (file vs directory)")
        
    finally:
        shutil.rmtree(temp_dir)
