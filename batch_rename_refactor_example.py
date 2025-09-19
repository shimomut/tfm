#!/usr/bin/env python3
"""
Example showing how to refactor the batch rename functionality 
to use SingleLineTextEdit class instead of manual text editing.

This demonstrates the before/after comparison and the benefits of using
the SingleLineTextEdit class.
"""

from src.tfm_single_line_text_edit import SingleLineTextEdit


class BatchRenameRefactorExample:
    """
    Example showing the refactored batch rename implementation
    using SingleLineTextEdit class
    """
    
    def __init__(self):
        # BEFORE: Multiple variables for text and cursor management
        # self.batch_rename_regex = ""
        # self.batch_rename_destination = ""
        # self.batch_rename_regex_cursor = 0
        # self.batch_rename_destination_cursor = 0
        # self.batch_rename_input_mode = 'regex'  # 'regex' or 'destination'
        
        # AFTER: Clean, encapsulated text editors
        self.regex_editor = SingleLineTextEdit()
        self.destination_editor = SingleLineTextEdit()
        self.active_field = 'regex'  # 'regex' or 'destination'
        
        # Other batch rename state
        self.batch_rename_files = []
        self.batch_rename_preview = []
        self.batch_rename_scroll = 0
        
    def get_active_editor(self):
        """Get the currently active text editor"""
        return self.regex_editor if self.active_field == 'regex' else self.destination_editor
    
    def get_regex_text(self):
        """Get the regex pattern text"""
        return self.regex_editor.get_text()
    
    def get_destination_text(self):
        """Get the destination pattern text"""
        return self.destination_editor.get_text()
    
    def handle_batch_rename_input_refactored(self, key):
        """
        REFACTORED: Handle input while in batch rename mode
        
        This version is much cleaner and shorter than the original
        because most of the text editing logic is handled by SingleLineTextEdit
        """
        if key == 27:  # ESC - cancel batch rename
            print("Batch rename cancelled")
            self.exit_batch_rename_mode()
            return True
            
        elif key == 9:  # Tab - switch between regex and destination input
            if self.active_field == 'regex':
                self.active_field = 'destination'
            else:
                self.active_field = 'regex'
            return True
            
        elif key == 10 or key == 13:  # Enter - perform batch rename
            if self.get_regex_text() and self.get_destination_text():
                self.perform_batch_rename()
            else:
                print("Please enter both regex pattern and destination pattern")
            return True
            
        elif key == 259:  # Up arrow - scroll preview up
            if self.batch_rename_scroll > 0:
                self.batch_rename_scroll -= 1
            return True
            
        elif key == 258:  # Down arrow - scroll preview down
            if self.batch_rename_preview and self.batch_rename_scroll < len(self.batch_rename_preview) - 1:
                self.batch_rename_scroll += 1
            return True
            
        else:
            # Let the active editor handle the key
            active_editor = self.get_active_editor()
            if active_editor.handle_key(key):
                # Text changed, update preview
                self.update_batch_rename_preview()
                return True
        
        return False
    
    def draw_batch_rename_dialog_refactored(self, stdscr):
        """
        REFACTORED: Draw the batch rename dialog
        
        This version is cleaner because the cursor highlighting logic
        is handled by the SingleLineTextEdit.draw() method
        """
        height, width = stdscr.getmaxyx()
        
        # Calculate dialog dimensions
        dialog_width = max(80, int(width * 0.9))
        dialog_height = max(25, int(height * 0.9))
        start_y = (height - dialog_height) // 2
        start_x = (width - dialog_width) // 2
        content_start_x = start_x + 2
        content_width = dialog_width - 4
        
        # Draw dialog background and border (same as before)
        # ... border drawing code ...
        
        # BEFORE: Complex cursor highlighting logic in _draw_input_field_with_cursor
        # AFTER: Simple, clean drawing with built-in cursor support
        
        # Draw regex input field
        regex_y = start_y + 2
        self.regex_editor.draw(
            stdscr, regex_y, content_start_x, content_width,
            "Regex Pattern: ",
            is_active=(self.active_field == 'regex')
        )
        
        # Draw destination input field  
        dest_y = start_y + 3
        self.destination_editor.draw(
            stdscr, dest_y, content_start_x, content_width,
            "Destination:   ",
            is_active=(self.active_field == 'destination')
        )
        
        # Draw help text and preview (same as before)
        # ... rest of dialog drawing ...
    
    def update_batch_rename_preview(self):
        """Update the batch rename preview"""
        # This method would use self.get_regex_text() and self.get_destination_text()
        # instead of accessing the raw variables
        pass
    
    def perform_batch_rename(self):
        """Perform the actual batch rename operation"""
        regex_pattern = self.get_regex_text()
        dest_pattern = self.get_destination_text()
        print(f"Performing batch rename: '{regex_pattern}' -> '{dest_pattern}'")
    
    def exit_batch_rename_mode(self):
        """Exit batch rename mode and clean up"""
        # Clear the editors
        self.regex_editor.clear()
        self.destination_editor.clear()
        self.active_field = 'regex'


def show_comparison():
    """Show the before/after comparison"""
    print("Batch Rename Refactoring with SingleLineTextEdit")
    print("=" * 50)
    print()
    
    print("BENEFITS OF REFACTORING:")
    print("------------------------")
    print("1. REDUCED CODE COMPLEXITY:")
    print("   - Original handle_batch_rename_input(): ~120 lines")
    print("   - Refactored version: ~40 lines")
    print("   - 67% reduction in code size!")
    print()
    
    print("2. ELIMINATED DUPLICATE LOGIC:")
    print("   - No more separate cursor management for regex/destination")
    print("   - No more duplicate key handling code")
    print("   - No more manual text insertion/deletion logic")
    print()
    
    print("3. IMPROVED MAINTAINABILITY:")
    print("   - Text editing logic is centralized in SingleLineTextEdit")
    print("   - Easier to add new text input fields")
    print("   - Consistent behavior across all text inputs")
    print()
    
    print("4. BETTER TESTABILITY:")
    print("   - SingleLineTextEdit can be tested independently")
    print("   - Batch rename logic is simplified and easier to test")
    print("   - Clear separation of concerns")
    print()
    
    print("5. REUSABILITY:")
    print("   - SingleLineTextEdit can be used for other dialogs")
    print("   - Rename dialog, create file dialog, search dialog, etc.")
    print("   - Consistent text editing experience across the application")
    print()
    
    print("REMOVED VARIABLES:")
    print("------------------")
    print("❌ self.batch_rename_regex")
    print("❌ self.batch_rename_destination") 
    print("❌ self.batch_rename_regex_cursor")
    print("❌ self.batch_rename_destination_cursor")
    print()
    
    print("ADDED VARIABLES:")
    print("----------------")
    print("✅ self.regex_editor = SingleLineTextEdit()")
    print("✅ self.destination_editor = SingleLineTextEdit()")
    print()
    
    print("REMOVED METHODS:")
    print("----------------")
    print("❌ _draw_input_field_with_cursor() - 60 lines of complex cursor logic")
    print()
    
    print("The SingleLineTextEdit class encapsulates all the text editing")
    print("functionality, making the code much cleaner and more maintainable!")


if __name__ == "__main__":
    show_comparison()
    
    # Demo the refactored functionality
    print("\n" + "=" * 50)
    print("DEMO: Refactored Batch Rename")
    print("=" * 50)
    
    dialog = BatchRenameRefactorExample()
    
    # Simulate some text input
    dialog.regex_editor.set_text("old_name")
    dialog.destination_editor.set_text("new_name")
    
    print(f"Regex pattern: '{dialog.get_regex_text()}'")
    print(f"Destination pattern: '{dialog.get_destination_text()}'")
    
    # Simulate key handling
    print("\nSimulating key presses...")
    dialog.active_field = 'regex'
    dialog.get_active_editor().handle_key(ord('_'))
    dialog.get_active_editor().handle_key(ord('v'))
    dialog.get_active_editor().handle_key(ord('2'))
    
    print(f"After typing '_v2': '{dialog.get_regex_text()}'")
    
    print("\nDemo complete!")