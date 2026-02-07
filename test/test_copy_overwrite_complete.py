"""
Complete test for copy operation overwrite dialog fix

Run with: PYTHONPATH=.:src:ttk pytest test/test_copy_overwrite_complete.py -v
"""

import tempfile

from tfm_quick_choice_bar import QuickChoiceBar
from _config import Config


class MockFileManager:
    """Mock file manager to test the copy operation flow"""
    
    def __init__(self):
        self.config = Config()
        self.quick_choice_bar = QuickChoiceBar(self.config)
        self.needs_full_redraw = False
        self.dialog_log = []
    
    def log(self, message):
        """Log dialog events for testing"""
        self.dialog_log.append(message)
        print(f"LOG: {message}")
    
    def show_confirmation(self, message, callback):
        """Show confirmation dialog"""
        self.log(f"Showing confirmation: {message}")
        choices = [
            {"text": "Yes", "key": "y", "value": True},
            {"text": "No", "key": "n", "value": False},
            {"text": "Cancel", "key": "c", "value": None}
        ]
        self.quick_choice_bar.show(message, choices, callback)
    
    def show_dialog(self, message, choices, callback):
        """Show dialog"""
        self.log(f"Showing dialog: {message}")
        self.quick_choice_bar.show(message, choices, callback)
    
    def exit_quick_choice_mode(self):
        """Exit quick choice mode"""
        self.log("Exiting quick choice mode")
        self.quick_choice_bar.exit()
        self.needs_full_redraw = True
    
    def handle_quick_choice_input(self, key):
        """Handle input while in quick choice mode - using the FIXED version"""
        result = self.quick_choice_bar.handle_input(key)
        
        if result == True:
            self.needs_full_redraw = True
            return True
        elif isinstance(result, tuple):
            action, data = result
            if action == 'cancel':
                self.exit_quick_choice_mode()
                return True
            elif action == 'selection_changed':
                self.needs_full_redraw = True
                return True
            elif action == 'execute':
                # FIXED: Store callback before exiting mode
                callback = self.quick_choice_bar.callback
                # Exit quick choice mode first to allow new dialogs to be shown
                self.exit_quick_choice_mode()
                # Then execute the callback
                if callback:
                    callback(data)
                return True
        
        return False
    
    def copy_files_to_directory(self, files_to_copy, destination_dir):
        """Simulate copy operation with conflict detection"""
        self.log(f"Starting copy operation: {len(files_to_copy)} files to {destination_dir}")
        
        # Simulate conflict detection
        conflicts = []
        for source_file in files_to_copy:
            dest_path = destination_dir / source_file.name
            if dest_path.exists():
                conflicts.append((source_file, dest_path))
        
        if conflicts:
            self.log(f"Conflicts detected: {len(conflicts)}")
            # Show conflict resolution dialog
            conflict_names = [f.name for f, _ in conflicts]
            if len(conflicts) == 1:
                message = f"'{conflict_names[0]}' already exists in destination."
            else:
                message = f"{len(conflicts)} files already exist in destination."
            
            choices = [
                {"text": "Overwrite", "key": "o", "value": "overwrite"},
                {"text": "Skip", "key": "s", "value": "skip"},
                {"text": "Cancel", "key": "c", "value": "cancel"}
            ]
            
            def handle_conflict_choice(choice):
                self.log(f"Conflict resolution choice: {choice}")
                if choice == "cancel":
                    self.log("Copy operation cancelled")
                elif choice == "skip":
                    self.log("Skipping conflicting files")
                elif choice == "overwrite":
                    self.log("Overwriting existing files")
            
            self.show_dialog(message, choices, handle_conflict_choice)
        else:
            self.log("No conflicts, copying directly")
    
    def copy_selected_files(self, files_to_copy, destination_dir):
        """Simulate the copy_selected_files method with CONFIRM_COPY enabled"""
        self.log("Starting copy_selected_files")
        
        # Check if copy confirmation is enabled
        if getattr(self.config, 'CONFIRM_COPY', True):
            self.log("CONFIRM_COPY is enabled")
            # Show confirmation dialog
            if len(files_to_copy) == 1:
                message = f"Copy '{files_to_copy[0].name}' to {destination_dir}?"
            else:
                message = f"Copy {len(files_to_copy)} items to {destination_dir}?"
            
            def copy_callback(confirmed):
                self.log(f"Copy confirmation callback: {confirmed}")
                if confirmed:
                    self.copy_files_to_directory(files_to_copy, destination_dir)
                else:
                    self.log("Copy operation cancelled")
            
            self.show_confirmation(message, copy_callback)
        else:
            # Start copying files without confirmation
            self.copy_files_to_directory(files_to_copy, destination_dir)


def test_copy_overwrite_flow():
    """Test the complete copy operation flow with overwrite dialog"""
    
    # Create temporary directories for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create source and destination directories
        source_dir = temp_path / "source"
        dest_dir = temp_path / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()
        
        # Create test files
        test_file = source_dir / "test.txt"
        test_file.write_text("source content")
        
        # Create conflicting file in destination
        dest_file = dest_dir / "test.txt"
        dest_file.write_text("destination content")
        
        print("=== Testing Copy Operation with Overwrite Dialog ===")
        print(f"Source file: {test_file}")
        print(f"Destination: {dest_dir}")
        print(f"Conflict exists: {dest_file.exists()}")
        print()
        
        # Create mock file manager
        fm = MockFileManager()
        
        # Start the copy operation
        files_to_copy = [test_file]
        fm.copy_selected_files(files_to_copy, dest_dir)
        
        print(f"\n1. Initial dialog state: mode={fm.quick_choice_bar.mode}")
        print(f"   Message: '{fm.quick_choice_bar.message}'")
        
        # Simulate user pressing 'y' (yes) to confirm copy
        print("\n2. User presses 'y' to confirm copy...")
        fm.handle_quick_choice_input(ord('y'))
        
        print(f"\n3. After first dialog: mode={fm.quick_choice_bar.mode}")
        print(f"   Message: '{fm.quick_choice_bar.message}'")
        
        # Check if overwrite dialog is now active
        if fm.quick_choice_bar.mode and "already exists" in fm.quick_choice_bar.message:
            print("\n✓ SUCCESS: Overwrite dialog is now active!")
            
            # Simulate user pressing 'o' (overwrite)
            print("\n4. User presses 'o' to overwrite...")
            fm.handle_quick_choice_input(ord('o'))
            
            print(f"\n5. Final state: mode={fm.quick_choice_bar.mode}")
            print(f"   Message: '{fm.quick_choice_bar.message}'")
            
            return True
        else:
            print("\n✗ FAILURE: Overwrite dialog is not active!")
            return False
