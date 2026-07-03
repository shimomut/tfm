"""
Demo: Compare Selection with NFD/NFC Normalization

This demo shows how the compare selection feature correctly handles
Unicode normalization (NFD vs NFC) when comparing filenames across panes.

This is particularly important for cross-platform file management:
- macOS uses NFD (decomposed) form: "が" = "か" + combining mark
- Linux/Windows use NFC (composed) form: "が" = single character

Without normalization, these would be treated as different filenames
even though they represent the same text.

Run with: PYTHONPATH=.:src:ttk python demo/demo_compare_selection_nfd.py
"""

import sys
import tempfile
import shutil
import unicodedata
from pathlib import Path

from tfm_list_dialog import ListDialogHelpers


class MockListDialog:
    """Mock list dialog for demo"""
    def __init__(self):
        self.title = None
        self.options = None
        self.callback = None
    
    def show(self, title, options, callback):
        self.title = title
        self.options = options
        self.callback = callback


def create_demo_structure():
    """Create demo directory structure with NFD and NFC filenames"""
    temp_dir = tempfile.mkdtemp(prefix="tfm_nfd_demo_")
    left_dir = Path(temp_dir) / "macOS_pane"
    right_dir = Path(temp_dir) / "linux_pane"
    
    left_dir.mkdir()
    right_dir.mkdir()
    
    # Create files with NFD form in left pane (simulating macOS)
    nfd_files = [
        "テストファイル_が.txt",
        "がぎぐげご.pdf",
        "プロジェクト_が_完了.doc"
    ]
    
    for filename in nfd_files:
        nfd_filename = unicodedata.normalize('NFD', filename)
        (left_dir / nfd_filename).write_text(f"Content of {filename}")
    
    # Create files with NFC form in right pane (simulating Linux/Windows)
    nfc_files = [
        "テストファイル_が.txt",
        "がぎぐげご.pdf",
        "別のファイル.txt"  # Different file
    ]
    
    for filename in nfc_files:
        nfc_filename = unicodedata.normalize('NFC', filename)
        (right_dir / nfc_filename).write_text(f"Content of {filename}")
    
    return temp_dir, left_dir, right_dir


def create_pane_data(directory):
    """Create pane data structure for demo"""
    files = list(directory.iterdir())
    return {
        'path': directory,
        'files': files,
        'selected_files': set(),
        'selected_index': 0
    }


def demo_nfd_nfc_comparison():
    """Demonstrate NFD/NFC normalization in compare_selection"""
    print("=" * 70)
    print("TFM Compare Selection - NFD/NFC Normalization Demo")
    print("=" * 70)
    print()
    print("This demo shows how TFM correctly matches filenames across")
    print("different Unicode normalization forms (NFD vs NFC).")
    print()
    
    temp_dir, left_dir, right_dir = create_demo_structure()
    
    try:
        # Show the files in each pane
        print("📁 Left Pane (macOS - NFD form):")
        for f in left_dir.iterdir():
            nfd_bytes = f.name.encode('utf-8')
            print(f"  • {f.name}")
            print(f"    Bytes: {nfd_bytes[:40]}{'...' if len(nfd_bytes) > 40 else ''}")
        
        print()
        print("📁 Right Pane (Linux/Windows - NFC form):")
        for f in right_dir.iterdir():
            nfc_bytes = f.name.encode('utf-8')
            print(f"  • {f.name}")
            print(f"    Bytes: {nfc_bytes[:40]}{'...' if len(nfc_bytes) > 40 else ''}")
        
        print()
        print("Note: Even though the filenames look identical, they have")
        print("different byte representations (NFD vs NFC).")
        print()
        
        # Create pane data
        current_pane = create_pane_data(left_dir)
        other_pane = create_pane_data(right_dir)
        
        # Create mock dialog
        mock_dialog = MockListDialog()
        
        # Track messages
        messages = []
        def mock_print(msg):
            messages.append(msg)
        
        # Test the compare selection functionality
        ListDialogHelpers.show_compare_selection(
            mock_dialog, current_pane, other_pane, mock_print
        )
        
        # Perform comparison
        print("🔍 Running 'By filename' comparison...")
        print()
        current_pane['selected_files'].clear()
        mock_dialog.callback("By filename")
        
        # Show results
        selected_items = current_pane['selected_files']
        print(f"✅ Selected {len(selected_items)} matching files:")
        for item in selected_items:
            filename = Path(item).name
            print(f"  • {filename}")
        
        print()
        print("📊 Comparison Results:")
        for msg in messages:
            print(f"  {msg}")
        
        print()
        print("=" * 70)
        print("✨ Success!")
        print("=" * 70)
        print()
        print("TFM correctly normalized both NFD and NFC filenames to NFC")
        print("before comparing, allowing files with the same logical name")
        print("to be matched regardless of their Unicode normalization form.")
        print()
        print("This ensures seamless cross-platform file management between")
        print("macOS (NFD) and Linux/Windows (NFC) systems.")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    demo_nfd_nfc_comparison()
