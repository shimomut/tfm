"""
Drag payload builder for drag-and-drop operations.

This module provides the DragPayloadBuilder class which prepares file paths
for drag operations, including validation and conversion to file:// URLs.
"""

from pathlib import Path
from typing import List, Optional
from urllib.parse import quote

from tfm_log_manager import getLogger


class DragPayloadBuilder:
    """Builds drag payload from file selections."""
    
    MAX_FILES = 1000  # Maximum files in a single drag
    
    def __init__(self):
        self.logger = getLogger("DragPayload")
        self.last_error_message = None  # Store last error for user feedback
    
    def build_payload(
        self,
        selected_files: List[Path],
        focused_item: Optional[Path],
        current_directory: Path
    ) -> Optional[List[str]]:
        """
        Build drag payload from file selections.
        
        Args:
            selected_files: List of selected file paths
            focused_item: Currently focused file path
            current_directory: Current directory path
            
        Returns:
            List of file:// URLs, or None if drag not allowed
        """
        # Clear previous error
        self.last_error_message = None
        # Determine which files to drag
        if selected_files:
            files_to_drag = selected_files
        elif focused_item:
            # Check if focused item is parent directory marker
            if focused_item.name == "..":
                self.logger.info("Cannot drag parent directory marker")
                # No error message for parent directory (expected behavior)
                return None
            files_to_drag = [focused_item]
        else:
            self.logger.warning("No files to drag")
            self.last_error_message = "No files selected for drag operation"
            return None
        
        # Check file count limit
        if len(files_to_drag) > self.MAX_FILES:
            self.logger.error(f"Too many files to drag: {len(files_to_drag)} > {self.MAX_FILES}")
            self.last_error_message = f"Cannot drag more than {self.MAX_FILES} files at once. You selected {len(files_to_drag)} files."
            return None
        
        # Validate and convert to URLs
        urls = []
        for file_path in files_to_drag:
            # Check if file is remote
            if self._is_remote_file(file_path):
                self.logger.error(f"Cannot drag remote file: {file_path}")
                self.last_error_message = "Cannot drag remote files (S3, SSH). Only local files can be dragged."
                return None
            
            # Check if file is inside archive
            if self._is_archive_content(file_path):
                self.logger.error(f"Cannot drag archive content: {file_path}")
                self.last_error_message = "Cannot drag files from within archives. Please extract the files first."
                return None
            
            # Check if file exists
            if not file_path.exists():
                self.logger.error(f"File does not exist: {file_path}")
                self.last_error_message = f"File no longer exists: {file_path.name}"
                return None
            
            # Convert to absolute file:// URL
            absolute_path = file_path.resolve()
            url = self._path_to_file_url(absolute_path)
            urls.append(url)
        
        self.logger.info(f"Built drag payload with {len(urls)} files")
        return urls
    
    def get_last_error(self) -> Optional[str]:
        """
        Get the last error message from payload building.
        
        Returns:
            Error message string, or None if no error
        """
        return self.last_error_message
    
    def _is_remote_file(self, path: Path) -> bool:
        """Check if path is a remote file (S3, SSH, etc.)."""
        path_str = str(path)
        return path_str.startswith("s3://") or path_str.startswith("ssh://")
    
    def _is_archive_content(self, path: Path) -> bool:
        """Check if path is inside an archive."""
        # Archive paths contain special markers
        path_str = str(path)
        return "::archive::" in path_str or ".zip/" in path_str or ".tar/" in path_str
    
    def _path_to_file_url(self, path: Path) -> str:
        """
        Convert file path to file:// URL.
        
        Args:
            path: Absolute file path
            
        Returns:
            file:// URL string
        """
        # Convert to POSIX path and URL-encode
        posix_path = path.as_posix()
        encoded_path = quote(posix_path, safe='/')
        return f"file://{encoded_path}"
