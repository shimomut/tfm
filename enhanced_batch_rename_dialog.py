#!/usr/bin/env python3
"""
Enhanced Batch Rename Dialog with Up/Down navigation

This demonstrates how to use the SingleLineTextEdit class in a batch rename dialog
where Up/Down arrow keys move focus between the regex and destination fields,
while Tab can still be used as an alternative.
"""

import curses
from src.tfm_single_line_text_edit import SingleLineTextEdit


class EnhancedBatchRenameDialog:
    """
    Enhanced batch rename dialog that uses Up/Down keys for field navigation
    and Ctrl+Up/Ctrl+Down for preview scrolling
    """
    
    def __init__(self):
        # Text editors for the two input fields
        self.regex_editor = SingleLineTextEdit()
        self.destination_editor = SingleLineTextEdit()
        
        # Track which field is currently active
        self.active_field = 'regex'  # 'regex' or 'destination'
        
        # Preview and scrolling state
        self.batch_rename_files = []
        self.batch_rename_preview = []
        self.batch_rename_scroll = 0
        
        # For demo purposes
        self.needs_full_redraw = False
        
    def get_active_editor(self):
        """Get the currently active text editor"""
        return self.regex_editor if self.active_field == 'regex' else self.destination_editor
    
    def switch_to_regex_field(self):
        """Switch focus to the regex field"""
        if self.active_field != 'regex':
            self.active_field = 'regex'
            return True
        return False
    
    def switch_to_destination_field(self):
        """Switch focus to the destination field"""
        if self.active_field != 'destination':
            self.active_field = 'destination'
            return True
        return False
    
    def handle_batch_rename_input(self, key):
        """
        Handle input while in batch rename mode with Up/Down field navigation
        
        Args:
            key (int): The key code from curses
            
        Returns:
            bool: True if the key was handled, False otherwise
        """
        # ESC - cancel batch rename
        if key == 27:
            print("Batch rename cancelled")
            self.exit_batch_rename_mode()
            return True
        
        # Tab - switch between fields (alternative to Up/Down)
        elif key == 9:  # Tab
            if self.active_field == 'regex':
                self.switch_to_destination_field()
            else:
                self.switch_to_regex_field()
            self.needs_full_redraw = True
            return True
        
        # Up arrow - move to previous field (regex)
        elif key == 259 or (hasattr(curses, 'KEY_UP') and key == curses.KEY_UP):
            if self.switch_to_regex_field():
                self.needs_full_redraw = True
            return True
        
        # Down arrow - move to next field (destination)
        elif key == 258 or (hasattr(curses, 'KEY_DOWN') and key == curses.KEY_DOWN):
            if self.switch_to_destination_field():
                self.needs_full_redraw = True
            return True
        
        # Ctrl+Up - scroll preview up
        elif key == 566:  # Ctrl+Up (this may vary by terminal)
            if self.batch_rename_scroll > 0:
                self.batch_rename_scroll -= 1
                self.needs_full_redraw = True
            return True
        
        # Ctrl+Down - scroll preview down  
        elif key == 525:  # Ctrl+Down (this may vary by terminal)
            if self.batch_rename_preview and self.batch_rename_scroll < len(self.batch_rename_preview) - 1:
                self.batch_rename_scroll += 1
                self.needs_full_redraw = True
            return True
        
        # Page Up - scroll preview up by page
        elif key == 339 or (hasattr(curses, 'KEY_PPAGE') and key == curses.KEY_PPAGE):
            self.batch_rename_scroll = max(0, self.batch_rename_scroll - 10)
            self.needs_full_redraw = True
            return True
        
        # Page Down - scroll preview down by page
        elif key == 338 or (hasattr(curses, 'KEY_NPAGE') and key == curses.KEY_NPAGE):
            if self.batch_rename_preview:
                max_scroll = max(0, len(self.batch_rename_preview) - 10)
                self.batch_rename_scroll = min(max_scroll, self.batch_rename_scroll + 10)
                self.needs_full_redraw = True
            return True
        
        # Enter - perform batch rename
        elif key == 10 or key == 13:  # Enter
            regex_text = self.regex_editor.get_text()
            dest_text = self.destination_editor.get_text()
            if regex_text and dest_text:
                print(f"Performing batch rename: '{regex_text}' -> '{dest_text}'")
                self.perform_batch_rename()
            else:
                print("Please enter both regex pattern and destination pattern")
            return True
        
        # Let the active editor handle other keys
        else:
            active_editor = self.get_active_editor()
            if active_editor.handle_key(key):
                # Text changed, update preview
                self.update_batch_rename_preview()
                self.needs_full_redraw = True
                return True
        
        return False
    
    def draw_batch_rename_dialog(self, stdscr):
        """
        Draw the enhanced batch rename dialog
        
        Args:
            stdscr: The curses screen object
        """
        height, width = stdscr.getmaxyx()
        
        # Calculate dialog dimensions
        dialog_width = max(80, int(width * 0.9))
        dialog_height = max(25, int(height * 0.9))
        start_y = (height - dialog_height) // 2
        start_x = (width - dialog_width) // 2
        content_start_x = start_x + 2
        content_width = dialog_width - 4
        
        # Draw dialog background and border
        self._draw_dialog_border(stdscr, start_y, start_x, dialog_width, dialog_height)
        
        # Draw title
        title_text = f" Enhanced Batch Rename ({len(self.batch_rename_files)} files) "
        title_x = start_x + (dialog_width - len(title_text)) // 2
        try:
            stdscr.addstr(start_y, title_x, title_text, curses.A_BOLD)
        except curses.error:
            pass
        
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
        
        # Draw navigation help
        help_y = start_y + 5
        help_text = "Navigation: ↑/↓ = Switch fields, Tab = Alt switch, PgUp/PgDn = Scroll preview"
        try:
            stdscr.addstr(help_y, content_start_x, help_text[:content_width], curses.A_DIM)
        except curses.error:
            pass
        
        # Draw macro help
        macro_help_y = start_y + 6
        macro_text = "Macros: \\0=full name, \\1-\\9=regex groups, \\d=index"
        try:
            stdscr.addstr(macro_help_y, content_start_x, macro_text[:content_width], curses.A_DIM)
        except curses.error:
            pass
        
        # Draw separator
        sep_y = start_y + 7
        sep_line = "─" * (content_width)
        try:
            stdscr.addstr(sep_y, content_start_x, sep_line, curses.A_DIM)
        except curses.error:
            pass
        
        # Draw preview section
        preview_start_y = start_y + 8
        preview_height = dialog_height - 10
        self._draw_preview_section(stdscr, preview_start_y, content_start_x, content_width, preview_height)
        
        # Draw status line
        status_y = start_y + dialog_height - 2
        active_field_indicator = f"Active: {self.active_field.upper()}"
        try:
            stdscr.addstr(status_y, content_start_x, active_field_indicator, curses.A_BOLD)
        except curses.error:
            pass
    
    def _draw_dialog_border(self, stdscr, start_y, start_x, width, height):
        """Draw the dialog border"""
        try:
            # Top border
            stdscr.addstr(start_y, start_x, "┌" + "─" * (width - 2) + "┐")
            
            # Side borders
            for y in range(start_y + 1, start_y + height - 1):
                stdscr.addstr(y, start_x, "│")
                stdscr.addstr(y, start_x + width - 1, "│")
            
            # Bottom border
            stdscr.addstr(start_y + height - 1, start_x, "└" + "─" * (width - 2) + "┘")
        except curses.error:
            pass
    
    def _draw_preview_section(self, stdscr, start_y, start_x, width, height):
        """Draw the preview section"""
        try:
            stdscr.addstr(start_y, start_x, "Preview:", curses.A_BOLD)
        except curses.error:
            pass
        
        # Draw preview items
        for i in range(min(height - 1, len(self.batch_rename_preview))):
            preview_y = start_y + 1 + i
            preview_index = self.batch_rename_scroll + i
            
            if preview_index < len(self.batch_rename_preview):
                preview_item = self.batch_rename_preview[preview_index]
                preview_text = f"{preview_index + 1:3d}. {preview_item}"
                try:
                    stdscr.addstr(preview_y, start_x + 2, preview_text[:width - 4])
                except curses.error:
                    pass
    
    def update_batch_rename_preview(self):
        """Update the batch rename preview based on current patterns"""
        regex_text = self.regex_editor.get_text()
        dest_text = self.destination_editor.get_text()
        
        # Simple demo preview generation
        self.batch_rename_preview = []
        if regex_text and dest_text:
            for i, filename in enumerate(self.batch_rename_files):
                # Simple replacement for demo (in real implementation, use regex)
                if regex_text in filename:
                    new_name = filename.replace(regex_text, dest_text)
                    self.batch_rename_preview.append(f"{filename} → {new_name}")
                else:
                    self.batch_rename_preview.append(f"{filename} (no match)")
    
    def perform_batch_rename(self):
        """Perform the actual batch rename operation"""
        print("Batch rename would be performed here")
        self.exit_batch_rename_mode()
    
    def exit_batch_rename_mode(self):
        """Exit batch rename mode and clean up"""
        self.regex_editor.clear()
        self.destination_editor.clear()
        self.active_field = 'regex'
        self.batch_rename_scroll = 0
        print("Exited batch rename mode")


def demo_enhanced_batch_rename():
    """Demo the enhanced batch rename dialog functionality"""
    print("Enhanced Batch Rename Dialog Demo")
    print("=" * 40)
    
    dialog = EnhancedBatchRenameDialog()
    
    # Set up some demo files
    dialog.batch_rename_files = [
        "old_file_1.txt",
        "old_file_2.txt", 
        "old_document.pdf",
        "old_image.jpg",
        "old_script.py"
    ]
    
    # Set some initial patterns
    dialog.regex_editor.set_text("old_")
    dialog.destination_editor.set_text("new_")
    dialog.update_batch_rename_preview()
    
    print(f"Demo files: {len(dialog.batch_rename_files)} files")
    print(f"Regex pattern: '{dialog.regex_editor.get_text()}'")
    print(f"Destination pattern: '{dialog.destination_editor.get_text()}'")
    print(f"Active field: {dialog.active_field}")
    
    print("\nKey handling demo:")
    
    # Test Up/Down navigation
    print("Testing Up/Down navigation...")
    
    # Start in regex field
    assert dialog.active_field == 'regex'
    
    # Down arrow should move to destination
    result = dialog.handle_batch_rename_input(258)  # KEY_DOWN
    assert result == True
    assert dialog.active_field == 'destination'
    print("✓ Down arrow moved to destination field")
    
    # Up arrow should move back to regex
    result = dialog.handle_batch_rename_input(259)  # KEY_UP
    assert result == True
    assert dialog.active_field == 'regex'
    print("✓ Up arrow moved to regex field")
    
    # Tab should also work
    result = dialog.handle_batch_rename_input(9)  # Tab
    assert result == True
    assert dialog.active_field == 'destination'
    print("✓ Tab moved to destination field")
    
    # Test text editing in active field
    active_editor = dialog.get_active_editor()
    active_editor.clear()
    active_editor.insert_char('t')
    active_editor.insert_char('e')
    active_editor.insert_char('s')
    active_editor.insert_char('t')
    
    print(f"✓ Text editing works: '{active_editor.get_text()}'")
    
    print("\n🎉 Enhanced batch rename demo completed successfully!")
    
    print("\nFeatures demonstrated:")
    print("- Up/Down arrows for field navigation")
    print("- Tab as alternative field switching")
    print("- Text editing in active field")
    print("- Preview updates")
    print("- Clean separation of concerns")


if __name__ == "__main__":
    demo_enhanced_batch_rename()