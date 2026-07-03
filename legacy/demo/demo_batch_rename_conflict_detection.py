#!/usr/bin/env python3
r"""
Demo: Batch Rename Conflict Detection

Demonstrates how BatchRenameDialog detects conflicts when multiple files
in the same batch would be renamed to the same name.

This demo shows:
1. Detection of duplicate new names within batch
2. Detection of conflicts with existing files
3. Mixed scenarios with both types of conflicts
4. How unique patterns avoid conflicts

Press ESC to exit each dialog.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ttk import TtkApplication, KeyCode
from tfm_batch_rename_dialog import BatchRenameDialog


class ConflictDetectionDemo(TtkApplication):
    """Demo application for batch rename conflict detection"""
    
    def __init__(self):
        super().__init__()
        self.dialog = None
        self.temp_dir = None
        self.demo_stage = 0
        self.stages = [
            self.demo_duplicate_names,
            self.demo_partial_duplicates,
            self.demo_existing_file_conflict,
            self.demo_unique_with_index,
            self.demo_unique_with_groups,
            self.demo_empty_replacement_conflict
        ]
        
    def setup(self):
        """Setup the demo"""
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create dialog
        config = {}
        self.dialog = BatchRenameDialog(config, self.renderer)
        
        # Start first demo
        self.next_demo()
        
    def cleanup(self):
        """Cleanup temporary files"""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def next_demo(self):
        """Move to next demo stage"""
        if self.demo_stage < len(self.stages):
            # Clean up previous files
            if self.temp_dir:
                for item in self.temp_dir.iterdir():
                    if item.is_file():
                        item.unlink()
            
            # Run next stage
            self.stages[self.demo_stage]()
            self.demo_stage += 1
        else:
            # All demos complete
            self.running = False
    
    def demo_duplicate_names(self):
        """Demo: Multiple files renamed to same name"""
        # Create test files
        file1 = self.temp_dir / "test1.txt"
        file2 = self.temp_dir / "test2.txt"
        file3 = self.temp_dir / "test3.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        file3.write_text("Content 3")
        
        # Show dialog
        self.dialog.show([file1, file2, file3])
        
        # Set pattern that creates duplicate names
        self.dialog.regex_editor.set_text(r"test\d")
        self.dialog.destination_editor.set_text("result")
        self.dialog.update_preview()
        
        # Add title
        self.demo_title = "Demo 1: Duplicate Names in Batch"
        self.demo_description = "All three files renamed to 'result.txt' - all marked as CONFLICT"
    
    def demo_partial_duplicates(self):
        """Demo: Only some files have duplicate names"""
        # Create test files
        file1 = self.temp_dir / "test1.txt"
        file2 = self.temp_dir / "test2.txt"
        file3 = self.temp_dir / "other.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        file3.write_text("Content 3")
        
        # Show dialog
        self.dialog.show([file1, file2, file3])
        
        # Set pattern that only affects test files
        self.dialog.regex_editor.set_text(r"test\d")
        self.dialog.destination_editor.set_text("result")
        self.dialog.update_preview()
        
        # Add title
        self.demo_title = "Demo 2: Partial Duplicates"
        self.demo_description = "test1 and test2 → 'result.txt' (CONFLICT), other.txt unchanged"
    
    def demo_existing_file_conflict(self):
        """Demo: Conflict with existing file"""
        # Create test files
        file1 = self.temp_dir / "test1.txt"
        file2 = self.temp_dir / "test2.txt"
        existing = self.temp_dir / "result.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        existing.write_text("Existing content")
        
        # Show dialog (not including existing file)
        self.dialog.show([file1, file2])
        
        # Set pattern that conflicts with existing file
        self.dialog.regex_editor.set_text(r"test1")
        self.dialog.destination_editor.set_text("result")
        self.dialog.update_preview()
        
        # Add title
        self.demo_title = "Demo 3: Existing File Conflict"
        self.demo_description = "test1 → 'result.txt' conflicts with existing file"
    
    def demo_unique_with_index(self):
        """Demo: Using \\d macro to create unique names"""
        # Create test files
        file1 = self.temp_dir / "test1.txt"
        file2 = self.temp_dir / "test2.txt"
        file3 = self.temp_dir / "test3.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        file3.write_text("Content 3")
        
        # Show dialog
        self.dialog.show([file1, file2, file3])
        
        # Set pattern using \d macro for unique names
        self.dialog.regex_editor.set_text(r"test\d")
        self.dialog.destination_editor.set_text(r"result\d")
        self.dialog.update_preview()
        
        # Add title
        self.demo_title = "Demo 4: Unique Names with \\d Macro"
        self.demo_description = "Using \\d creates unique names: result1, result2, result3 - no conflicts"
    
    def demo_unique_with_groups(self):
        """Demo: Using regex groups to preserve uniqueness"""
        # Create test files
        file1 = self.temp_dir / "test_a_file.txt"
        file2 = self.temp_dir / "test_b_file.txt"
        file3 = self.temp_dir / "test_c_file.txt"
        file1.write_text("Content A")
        file2.write_text("Content B")
        file3.write_text("Content C")
        
        # Show dialog
        self.dialog.show([file1, file2, file3])
        
        # Set pattern using regex group to preserve unique part
        self.dialog.regex_editor.set_text(r"test_([abc])_file")
        self.dialog.destination_editor.set_text(r"result_\1")
        self.dialog.update_preview()
        
        # Add title
        self.demo_title = "Demo 5: Unique Names with Regex Groups"
        self.demo_description = "Using \\1 preserves unique part: result_a, result_b, result_c - no conflicts"
    
    def demo_empty_replacement_conflict(self):
        """Demo: Empty replacement creating conflicts"""
        # Create test files
        file1 = self.temp_dir / "prefix1_file.txt"
        file2 = self.temp_dir / "prefix2_file.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        
        # Show dialog
        self.dialog.show([file1, file2])
        
        # Remove prefix, creating duplicate names
        self.dialog.regex_editor.set_text(r"^prefix\d_")
        self.dialog.destination_editor.set_text("")
        self.dialog.update_preview()
        
        # Add title
        self.demo_title = "Demo 6: Empty Replacement Conflict"
        self.demo_description = "Removing prefixes creates duplicates: both → 'file.txt' - CONFLICT"
    
    def draw(self):
        """Draw the demo"""
        if not self.dialog or not self.dialog.is_active:
            return
        
        # Draw dialog
        self.dialog.draw()
        
        # Draw demo title and description at top
        if hasattr(self, 'demo_title'):
            height, width = self.renderer.get_dimensions()
            title_y = 1
            desc_y = 2
            
            # Center title
            title_x = (width - len(self.demo_title)) // 2
            self.renderer.draw_text(title_y, title_x, self.demo_title)
            
            # Center description
            desc_x = (width - len(self.demo_description)) // 2
            self.renderer.draw_text(desc_y, desc_x, self.demo_description)
    
    def handle_key(self, key_event):
        """Handle key events"""
        if not self.dialog or not self.dialog.is_active:
            return False
        
        # Let dialog handle the key
        if self.dialog.handle_key_event(key_event):
            return True
        
        # ESC closes current demo and moves to next
        if key_event.key_code == KeyCode.ESCAPE:
            self.dialog.exit()
            self.next_demo()
            return True
        
        return False


def main():
    """Run the demo"""
    demo = ConflictDetectionDemo()
    try:
        demo.run()
    finally:
        demo.cleanup()


if __name__ == "__main__":
    main()
