#!/usr/bin/env python3
r"""
Demo: Batch Rename Emoji Status Indicators

Demonstrates how BatchRenameDialog uses colored emoji status indicators to save space
and provide clear visual feedback.

Status indicators:
- (no icon) = Unchanged file
- 🟢 (Green circle) = Valid rename, ready to execute
- 🔴 (Red circle) = Conflict or invalid name

This demo shows:
1. Unchanged files with no status icon
2. Valid renames with green circle emoji
3. Conflicts with red circle emoji
4. Invalid names with red circle emoji
5. Space savings compared to text status

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


class EmojiStatusDemo(TtkApplication):
    """Demo application for emoji status indicators"""
    
    def __init__(self):
        super().__init__()
        self.dialog = None
        self.temp_dir = None
        self.demo_stage = 0
        self.stages = [
            self.demo_unchanged_files,
            self.demo_valid_renames,
            self.demo_conflicts,
            self.demo_invalid_names,
            self.demo_mixed_status
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
    
    def demo_unchanged_files(self):
        """Demo: Unchanged files show no status icon"""
        # Create test files
        file1 = self.temp_dir / "document.txt"
        file2 = self.temp_dir / "image.png"
        file3 = self.temp_dir / "data.csv"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        file3.write_text("Content 3")
        
        # Show dialog with no pattern (all unchanged)
        self.dialog.show([file1, file2, file3])
        self.dialog.regex_editor.set_text("")
        self.dialog.destination_editor.set_text("")
        self.dialog.update_preview()
        
        # Add title
        self.demo_title = "Demo 1: Unchanged Files"
        self.demo_description = "No pattern specified - all files show no status icon (unchanged)"
    
    def demo_valid_renames(self):
        """Demo: Valid renames show green circle emoji (🟢)"""
        # Create test files
        file1 = self.temp_dir / "old_name_1.txt"
        file2 = self.temp_dir / "old_name_2.txt"
        file3 = self.temp_dir / "old_name_3.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        file3.write_text("Content 3")
        
        # Show dialog with valid rename pattern
        self.dialog.show([file1, file2, file3])
        self.dialog.regex_editor.set_text(r"old_name")
        self.dialog.destination_editor.set_text("new_name")
        self.dialog.update_preview()
        
        # Add title
        self.demo_title = "Demo 2: Valid Renames (🟢)"
        self.demo_description = "Valid rename pattern - all files show green circle emoji (🟢) for OK"
    
    def demo_conflicts(self):
        """Demo: Conflicts show red circle emoji (🔴)"""
        # Create test files
        file1 = self.temp_dir / "test1.txt"
        file2 = self.temp_dir / "test2.txt"
        file3 = self.temp_dir / "test3.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        file3.write_text("Content 3")
        
        # Show dialog with conflicting pattern
        self.dialog.show([file1, file2, file3])
        self.dialog.regex_editor.set_text(r"test\d")
        self.dialog.destination_editor.set_text("result")
        self.dialog.update_preview()
        
        # Add title
        self.demo_title = "Demo 3: Conflicts (🔴)"
        self.demo_description = "All files renamed to same name - red circle emoji (🔴) for conflict"
    
    def demo_invalid_names(self):
        """Demo: Invalid names show red circle emoji (🔴)"""
        # Create test files
        file1 = self.temp_dir / "document.txt"
        file2 = self.temp_dir / "image.png"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        
        # Show dialog with pattern that creates invalid names
        self.dialog.show([file1, file2])
        self.dialog.regex_editor.set_text(r".*")
        self.dialog.destination_editor.set_text("")
        self.dialog.update_preview()
        
        # Add title
        self.demo_title = "Demo 4: Invalid Names (🔴)"
        self.demo_description = "Empty filename result - red circle emoji (🔴) for invalid"
    
    def demo_mixed_status(self):
        """Demo: Mixed status indicators"""
        # Create test files
        file1 = self.temp_dir / "test1.txt"
        file2 = self.temp_dir / "test2.txt"
        file3 = self.temp_dir / "other.txt"
        file4 = self.temp_dir / "data.csv"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        file3.write_text("Content 3")
        file4.write_text("Content 4")
        
        # Show dialog with pattern that creates mixed results
        self.dialog.show([file1, file2, file3, file4])
        self.dialog.regex_editor.set_text(r"test\d")
        self.dialog.destination_editor.set_text("result")
        self.dialog.update_preview()
        
        # Add title
        self.demo_title = "Demo 5: Mixed Status"
        self.demo_description = "test1,test2 → conflict (🔴), other.txt → unchanged (no icon), data.csv → unchanged (no icon)"
    
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
    demo = EmojiStatusDemo()
    try:
        demo.run()
    finally:
        demo.cleanup()


if __name__ == "__main__":
    main()
