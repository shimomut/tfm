#!/usr/bin/env python3
"""
Demo script showing the enhanced Compare & Select feature that now works with both files and directories.

This demo creates a sample directory structure and demonstrates how the compare selection
feature can now select both files and directories based on various comparison criteria.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_list_dialog import ListDialogHelpers


class DemoListDialog:
    """Demo list dialog that shows the selection process"""
    def __init__(self):
        self.title = None
        self.options = None
        self.callback = None
    
    def show(self, title, options, callback):
        self.title = title
        self.options = options
        self.callback = callback
        
        print(f"\n📋 {title}")
        print("=" * 50)
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")


def create_demo_structure():
    """Create demo directory structure"""
    temp_dir = tempfile.mkdtemp(prefix="tfm_demo_")
    left_dir = Path(temp_dir) / "project_v1"
    right_dir = Path(temp_dir) / "project_v2"
    
    left_dir.mkdir()
    right_dir.mkdir()
    
    print(f"📁 Created demo directories:")
    print(f"   Left:  {left_dir}")
    print(f"   Right: {right_dir}")
    
    # Create project structure in left pane (v1)
    (left_dir / "README.md").write_text("# Project v1")
    (left_dir / "config.json").write_text('{"version": "1.0"}')
    (left_dir / "main.py").write_text("print('Hello v1')")
    (left_dir / "src").mkdir()
    (left_dir / "src" / "utils.py").write_text("def helper(): pass")
    (left_dir / "docs").mkdir()
    (left_dir / "docs" / "guide.md").write_text("# Guide v1")
    (left_dir / "tests").mkdir()
    (left_dir / "old_feature.py").write_text("# Deprecated")
    
    # Create project structure in right pane (v2) - some matching, some different
    (right_dir / "README.md").write_text("# Project v2")  # Same name, different content
    (right_dir / "config.json").write_text('{"version": "1.0"}')  # Same name, same content
    (right_dir / "main.py").write_text("print('Hello v2')")  # Same name, different content
    (right_dir / "src").mkdir()  # Same directory name
    (right_dir / "src" / "utils.py").write_text("def helper(): pass")  # Same file
    (right_dir / "docs").mkdir()  # Same directory name
    (right_dir / "docs" / "guide.md").write_text("# Guide v2")  # Same name, different content
    (right_dir / "lib").mkdir()  # Different directory name
    (right_dir / "new_feature.py").write_text("# New in v2")  # New file
    
    return temp_dir, left_dir, right_dir


def create_pane_data(directory):
    """Create pane data structure"""
    files = sorted(directory.iterdir())  # Sort for consistent display
    return {
        'path': directory,
        'files': files,
        'selected_files': set(),
        'selected_index': 0
    }


def display_pane_contents(pane_name, pane_data):
    """Display contents of a pane"""
    print(f"\n📂 {pane_name} Pane Contents:")
    for item in pane_data['files']:
        if item.is_dir():
            print(f"   📁 {item.name}/")
        else:
            print(f"   📄 {item.name}")


def display_selection_results(pane_data, criteria):
    """Display the selection results"""
    if not pane_data['selected_files']:
        print("   ❌ No items selected")
        return
    
    selected_items = []
    for item_path_str in pane_data['selected_files']:
        item_path = Path(item_path_str)
        if item_path.is_dir():
            selected_items.append(f"📁 {item_path.name}/")
        else:
            selected_items.append(f"📄 {item_path.name}")
    
    print(f"\n✅ Selected {len(selected_items)} items using '{criteria}':")
    for item in sorted(selected_items):
        print(f"   {item}")


def demo_compare_selection():
    """Demonstrate the enhanced compare selection feature"""
    print("🎯 TFM Compare & Select Feature Demo")
    print("Enhanced to work with both files and directories!")
    print("=" * 60)
    
    temp_dir, left_dir, right_dir = create_demo_structure()
    
    try:
        # Create pane data
        left_pane = create_pane_data(left_dir)
        right_pane = create_pane_data(right_dir)
        
        # Display initial contents
        display_pane_contents("Left (project_v1)", left_pane)
        display_pane_contents("Right (project_v2)", right_pane)
        
        # Create demo dialog
        demo_dialog = DemoListDialog()
        
        # Track messages
        messages = []
        def capture_print(msg):
            messages.append(msg)
        
        # Set up the compare selection
        ListDialogHelpers.show_compare_selection(
            demo_dialog, left_pane, right_pane, capture_print
        )
        
        print(f"\n🔍 Available comparison criteria:")
        for i, option in enumerate(demo_dialog.options, 1):
            print(f"   {i}. {option}")
        
        # Demo each comparison type
        comparison_types = [
            ("By filename", "Selects items with matching names (regardless of content)"),
            ("By filename and size", "Selects items with matching names and sizes"),
            ("By filename, size, and timestamp", "Selects items with matching names, sizes, and modification times")
        ]
        
        for criteria, description in comparison_types:
            print(f"\n" + "─" * 60)
            print(f"🧪 Testing: {criteria}")
            print(f"📝 {description}")
            
            # Clear previous selection
            left_pane['selected_files'].clear()
            messages.clear()
            
            # Run the comparison
            demo_dialog.callback(criteria)
            
            # Display results
            display_selection_results(left_pane, criteria)
            
            # Show the feedback message
            if messages:
                print(f"\n💬 System message: {messages[-1]}")
        
        print(f"\n" + "=" * 60)
        print("🎉 Demo completed!")
        print("\nKey improvements in this enhancement:")
        print("✅ Now works with both files AND directories")
        print("✅ Type-safe matching (files match files, directories match directories)")
        print("✅ Intelligent size comparison (skipped for directories)")
        print("✅ Enhanced user feedback with item type counts")
        print("✅ Robust error handling for filesystem operations")
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Cleaned up demo files")


if __name__ == "__main__":
    demo_compare_selection()