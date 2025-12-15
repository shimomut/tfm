#!/usr/bin/env python3
"""
TUI File Manager - Drives Dialog Component
Provides storage/drive selection functionality including local filesystem and S3 buckets
"""

import threading
import time
from ttk import KeyCode, TextAttribute
from tfm_path import Path
from tfm_base_list_dialog import BaseListDialog
from tfm_colors import get_status_color
from tfm_progress_animator import ProgressAnimatorFactory
from tfm_input_compat import ensure_input_event

# AWS S3 support - import boto3 with fallback
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    boto3 = None
    ClientError = Exception
    NoCredentialsError = Exception


class DriveEntry:
    """Represents a drive/storage entry in the drives dialog"""
    
    def __init__(self, name, path, drive_type, description=None):
        self.name = name
        self.path = path
        self.drive_type = drive_type  # 'local', 's3'
        self.description = description or ""
    
    def __str__(self):
        return self.name
    
    def get_display_text(self):
        """Get formatted display text for this drive entry"""
        if self.drive_type == 'local':
            icon = "🏠" if "Home" in self.name else "📁"
            display_name = self.name
        elif self.drive_type == 's3':
            icon = "☁️ " # Add extra white space as this emoji is half-width on terminals.
            # Add s3:// scheme prefix for S3 buckets (unless it's an error/status entry)
            if self.path and not self.name.startswith("S3 ("):
                display_name = f"s3://{self.name}"
            else:
                display_name = self.name
        else:
            icon = "💾"
            display_name = self.name
        
        if self.description:
            return f"{icon} {display_name} - {self.description}"
        else:
            return f"{icon} {display_name}"


class DrivesDialog(BaseListDialog):
    """Drives dialog component for storage/drive selection"""
    
    def __init__(self, config, renderer=None):
        super().__init__(config, renderer)
        
        # Drives dialog specific state
        self.drives = []  # List of all available drives
        self.filtered_drives = []  # Filtered drives based on search
        self.loading_s3 = False  # Whether S3 bucket scan is in progress
        self.content_changed = True  # Track if content needs redraw
        
        # Threading support for S3 bucket loading
        self.s3_thread = None
        self.s3_lock = threading.Lock()
        self.cancel_s3_scan = threading.Event()
        
        # Animation support
        self.progress_animator = ProgressAnimatorFactory.create_search_animator(config)
        
    def show(self):
        """Show the drives dialog and start loading available drives"""
        # Cancel any existing S3 scan first
        self._cancel_current_s3_scan()
        
        self.is_active = True
        self.text_editor.clear()
        self.drives = []
        self.content_changed = True
        self.filtered_drives = []
        self.selected = 0
        self.scroll = 0
        self.loading_s3 = False
        
        # Reset animation
        self.progress_animator.reset()
        
        # Load local drives immediately
        self._load_local_drives()
        
        # Start S3 bucket loading in background
        self._start_s3_bucket_scan()
        
    def exit(self):
        """Exit drives dialog mode"""
        # Cancel any running S3 scan
        self._cancel_current_s3_scan()
        
        super().exit()
        self.drives = []
        self.filtered_drives = []
        self.loading_s3 = False
        self.content_changed = True
        
        # Reset animation
        self.progress_animator.reset()
        
    def handle_input(self, event):
        """Handle input while in drives dialog mode
        
        Args:
            event: KeyEvent from TTK renderer (or integer key code for backward compatibility)
        """
        # Backward compatibility: convert integer key codes to KeyEvent
        event = ensure_input_event(event)
        
        # Use base class navigation handling with thread safety
        with self.s3_lock:
            current_filtered = self.filtered_drives.copy()
        
        result = self.handle_common_navigation(event, current_filtered)
        
        if result == 'cancel':
            # Cancel S3 scan before exiting
            self._cancel_current_s3_scan()
            self.exit()
            return True
        elif result == 'select':
            # Cancel S3 scan before navigating
            self._cancel_current_s3_scan()
            
            # Return the selected drive for navigation (thread-safe)
            with self.s3_lock:
                if self.filtered_drives and 0 <= self.selected < len(self.filtered_drives):
                    selected_drive = self.filtered_drives[self.selected]
                    return ('navigate', selected_drive)
            return ('navigate', None)
        elif result == 'text_changed':
            self._filter_drives()
            self.content_changed = True
            return True
        elif result:
            # Update selection in thread-safe manner for navigation keys
            if event.key_code in [KeyCode.UP, KeyCode.DOWN, KeyCode.PAGE_UP, KeyCode.PAGE_DOWN, KeyCode.HOME, KeyCode.END]:
                with self.s3_lock:
                    # The base class already updated self.selected, just need to adjust scroll
                    self._adjust_scroll(len(self.filtered_drives))
            
            # Mark content as changed for ANY handled key to ensure continued rendering
            self.content_changed = True
            return True
            
        return False
    
    def _load_local_drives(self):
        """Load local filesystem drives/locations"""
        local_drives = []
        
        # Add home directory
        home_path = Path.home()
        local_drives.append(DriveEntry(
            name="Home Directory",
            path=str(home_path),
            drive_type="local",
            description=str(home_path)
        ))
        
        # Add root directory
        root_path = Path("/")
        local_drives.append(DriveEntry(
            name="Root Directory",
            path="/",
            drive_type="local",
            description="System root"
        ))
        

        
        # Add common directories if they exist
        common_dirs = [
            ("Documents", "~/Documents"),
            ("Downloads", "~/Downloads"),
            ("Desktop", "~/Desktop"),
        ]
        
        for name, path_str in common_dirs:
            try:
                path_obj = Path(path_str).expanduser()
                if path_obj.exists() and path_obj.is_dir():
                    # Avoid duplicates
                    if not any(drive.path == str(path_obj) for drive in local_drives):
                        local_drives.append(DriveEntry(
                            name=name,
                            path=str(path_obj),
                            drive_type="local",
                            description=str(path_obj)
                        ))
            except (OSError, PermissionError):
                continue
        
        # Update drives list (thread-safe)
        with self.s3_lock:
            self.drives.extend(local_drives)
            self._filter_drives_internal()
            self.content_changed = True
    
    def _start_s3_bucket_scan(self):
        """Start asynchronous S3 bucket scanning"""
        if not HAS_BOTO3:
            return  # Skip S3 scanning if boto3 not available
        
        # Cancel any existing scan
        self._cancel_current_s3_scan()
        
        # Start new scan thread
        self.cancel_s3_scan.clear()
        self.loading_s3 = True
        
        # Reset animation for new scan
        self.progress_animator.reset()
        
        self.s3_thread = threading.Thread(
            target=self._s3_scan_worker,
            daemon=True
        )
        self.s3_thread.start()
    
    def _cancel_current_s3_scan(self):
        """Cancel the current S3 bucket scan operation"""
        if self.s3_thread and self.s3_thread.is_alive():
            self.cancel_s3_scan.set()
            # Give the thread a moment to finish
            self.s3_thread.join(timeout=0.1)
        
        self.loading_s3 = False
        self.s3_thread = None
        self.content_changed = True
    
    def _s3_scan_worker(self):
        """Worker thread for performing the actual S3 bucket scan"""
        s3_drives = []
        
        try:
            # Initialize S3 client
            s3_client = boto3.client('s3')
            
            # List all buckets
            response = s3_client.list_buckets()
            
            for bucket in response.get('Buckets', []):
                # Check for cancellation
                if self.cancel_s3_scan.is_set():
                    return
                
                bucket_name = bucket['Name']
                
                s3_drives.append(DriveEntry(
                    name=bucket_name,
                    path=f"s3://{bucket_name}/",
                    drive_type="s3",
                    description=None
                ))
                
        except NoCredentialsError:
            # Add a placeholder entry indicating credentials are needed
            s3_drives.append(DriveEntry(
                name="S3 (No Credentials)",
                path="",
                drive_type="s3",
                description="Configure AWS credentials to access S3 buckets"
            ))
        except ClientError as e:
            # Add a placeholder entry indicating an error occurred
            error_msg = str(e)
            if len(error_msg) > 50:
                error_msg = error_msg[:47] + "..."
            s3_drives.append(DriveEntry(
                name="S3 (Error)",
                path="",
                drive_type="s3",
                description=f"Error: {error_msg}"
            ))
        except Exception as e:
            # Add a placeholder entry for unexpected errors
            error_msg = str(e)
            if len(error_msg) > 50:
                error_msg = error_msg[:47] + "..."
            s3_drives.append(DriveEntry(
                name="S3 (Unavailable)",
                path="",
                drive_type="s3",
                description=f"Error: {error_msg}"
            ))
        
        # Final update of results if not cancelled
        if not self.cancel_s3_scan.is_set():
            with self.s3_lock:
                self.drives.extend(s3_drives)
                self._filter_drives_internal()
                self.loading_s3 = False
                self.content_changed = True
    
    def _filter_drives(self):
        """Filter drives based on current search pattern (thread-safe)"""
        with self.s3_lock:
            self._filter_drives_internal()
            self.content_changed = True
    
    def _filter_drives_internal(self):
        """Internal method to filter drives (must be called with lock held)"""
        # Remember currently selected drive if any
        currently_selected_drive = None
        if self.filtered_drives and 0 <= self.selected < len(self.filtered_drives):
            currently_selected_drive = self.filtered_drives[self.selected]
        
        search_text = self.text_editor.text.strip()
        if not search_text:
            self.filtered_drives = self.drives.copy()
        else:
            search_lower = search_text.lower()
            self.filtered_drives = [
                drive for drive in self.drives 
                if (search_lower in drive.name.lower() or 
                    search_lower in drive.description.lower() or
                    search_lower in drive.path.lower())
            ]
        
        # Try to preserve selection if the previously selected drive is still in filtered results
        new_selected = 0
        if currently_selected_drive and currently_selected_drive in self.filtered_drives:
            try:
                new_selected = self.filtered_drives.index(currently_selected_drive)
            except ValueError:
                new_selected = 0
        
        # Update selection and adjust scroll
        self.selected = new_selected
        self._adjust_scroll(len(self.filtered_drives))
    
    def needs_redraw(self):
        """Check if this dialog needs to be redrawn"""
        # Always redraw when loading S3 to animate progress indicator
        return self.content_changed or self.loading_s3
    
    def draw(self):
        """Draw the drives dialog overlay"""
        # Draw dialog frame
        start_y, start_x, dialog_width, dialog_height = self.draw_dialog_frame(
            "Select Drive/Storage", 0.7, 0.8, 50, 18
        )
        
        # Draw filter input
        search_y = start_y + 2
        self.draw_text_input(search_y, start_x, dialog_width, "Filter: ")
        
        # Draw separator
        sep_y = start_y + 3
        self.draw_separator(sep_y, start_x, dialog_width)
        
        # Draw status with animated progress indicator (thread-safe)
        status_y = start_y + 4
        height, width = self.renderer.get_dimensions()
        if status_y < height:
            with self.s3_lock:
                drive_count = len(self.drives)
                filtered_count = len(self.filtered_drives)
                is_loading = self.loading_s3
                
                if is_loading:
                    # Get animated status text
                    s3_count = sum(1 for drive in self.drives if drive.drive_type == 's3')
                    local_count = sum(1 for drive in self.drives if drive.drive_type == 'local')
                    context_info = f"{local_count} local, {s3_count} S3"
                    
                    status_text = self.progress_animator.get_status_text("Loading S3", context_info, is_loading)
                    
                    # Use brighter color for active loading
                    color_pair, _ = get_status_color()
                    attributes = TextAttribute.BOLD
                else:
                    if self.text_editor.text.strip():
                        status_text = f"Drives: {filtered_count} (filtered from {drive_count})"
                    else:
                        s3_count = sum(1 for drive in self.drives if drive.drive_type == 's3')
                        local_count = sum(1 for drive in self.drives if drive.drive_type == 'local')
                        status_text = f"Drives: {drive_count} ({local_count} local, {s3_count} S3)"
                    
                    color_pair, attributes = get_status_color()
            
            self.renderer.draw_text(status_y, start_x + 2, status_text[:dialog_width - 4], color_pair, attributes)
        
        # Calculate results area
        results_start_y = start_y + 5
        results_end_y = start_y + dialog_height - 3
        content_start_x = start_x + 2
        content_width = dialog_width - 4
        
        # Format drives for display
        def format_drive(drive):
            return drive.get_display_text()
        
        # Draw results (thread-safe)
        with self.s3_lock:
            current_filtered = self.filtered_drives.copy()
        
        self.draw_list_items(current_filtered, 
                           results_start_y, results_end_y, content_start_x, content_width, format_drive)
        
        # Draw scrollbar
        scrollbar_x = start_x + dialog_width - 2
        content_height = results_end_y - results_start_y + 1
        self.draw_scrollbar(current_filtered, 
                          results_start_y, content_height, scrollbar_x)
        
        # Draw help text
        help_text = "Enter: Select | Type: Filter | ESC: Cancel"
        help_y = start_y + dialog_height - 2
        self.draw_help_text(help_text, help_y, start_x, dialog_width)
        
        # Automatically mark as not needing redraw after drawing (unless still loading)
        if not self.loading_s3:
            self.content_changed = False


class DrivesDialogHelpers:
    """Helper functions for drives dialog navigation and integration"""
    
    @staticmethod
    def navigate_to_drive(drive_entry, pane_manager, print_func):
        """Navigate to the selected drive/storage
        
        Args:
            drive_entry: DriveEntry object of the drive to navigate to
            pane_manager: PaneManager instance
            print_func: Function to print messages
        """
        if not drive_entry or not drive_entry.path:
            print_func("Error: Invalid drive selection")
            return
        
        current_pane = pane_manager.get_current_pane()
        
        try:
            # Create Path object for the drive
            drive_path = Path(drive_entry.path)
            
            # Validate the path exists and is accessible
            if drive_entry.drive_type == 'local':
                if not drive_path.exists() or not drive_path.is_dir():
                    print_func(f"Error: Drive path no longer exists or is not accessible: {drive_entry.path}")
                    return
            elif drive_entry.drive_type == 's3':
                # For S3, we'll let the S3PathImpl handle validation
                pass
            
            # Update the current pane
            old_path = current_pane['path']
            current_pane['path'] = drive_path
            current_pane['selected_index'] = 0
            current_pane['scroll_offset'] = 0
            current_pane['selected_files'].clear()
            
            pane_name = "left" if pane_manager.active_pane == 'left' else "right"
            print_func(f"Switched to {drive_entry.name}: {drive_entry.path}")
            
        except Exception as e:
            print_func(f"Error: Failed to navigate to drive: {e}")