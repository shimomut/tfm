#!/usr/bin/env python3
"""
TFM Archive Operations - Handles archive creation and extraction with cross-storage support
"""

import os
import tempfile
import tarfile
import zipfile
import gzip
import bz2
import lzma
import shutil
from pathlib import Path as PathlibPath
from tfm_path import Path
from tfm_progress_manager import ProgressManager, OperationType
from typing import List, Optional, Union, Tuple


class ArchiveOperations:
    """Handles archive creation and extraction operations with cross-storage support"""
    
    # Supported archive formats
    SUPPORTED_FORMATS = {
        '.tar': {'type': 'tar', 'compression': None},
        '.tar.gz': {'type': 'tar', 'compression': 'gz'},
        '.tgz': {'type': 'tar', 'compression': 'gz'},
        '.tar.bz2': {'type': 'tar', 'compression': 'bz2'},
        '.tbz2': {'type': 'tar', 'compression': 'bz2'},
        '.tar.xz': {'type': 'tar', 'compression': 'xz'},
        '.txz': {'type': 'tar', 'compression': 'xz'},
        '.zip': {'type': 'zip', 'compression': None},
        '.gz': {'type': 'gzip', 'compression': None},
        '.bz2': {'type': 'bzip2', 'compression': None},
        '.xz': {'type': 'xz', 'compression': None},
    }
    
    def __init__(self, log_manager=None, cache_manager=None, progress_manager=None):
        """Initialize archive operations with optional logging, cache management, and progress tracking"""
        self.log_manager = log_manager
        self.cache_manager = cache_manager
        self.progress_manager = progress_manager
    
    def _log(self, message: str, level: str = "INFO"):
        """Log a message if log manager is available"""
        if self.log_manager:
            self.log_manager.add_message(message, level)
    
    def get_archive_format(self, filename: str) -> Optional[dict]:
        """
        Determine archive format from filename
        
        Args:
            filename: Name of the archive file
            
        Returns:
            Dictionary with format info or None if not supported
        """
        filename_lower = filename.lower()
        
        # Check for compound extensions first (e.g., .tar.gz)
        for ext, format_info in self.SUPPORTED_FORMATS.items():
            if filename_lower.endswith(ext):
                return format_info
        
        return None
    
    def is_archive(self, path: Path) -> bool:
        """
        Check if a file is a supported archive format
        
        Args:
            path: Path to check
            
        Returns:
            True if file is a supported archive format
        """
        if not path.is_file():
            return False
        
        return self.get_archive_format(path.name) is not None
    
    def create_archive(self, source_paths: List[Path], archive_path: Path, 
                      format_type: str = 'tar.gz') -> bool:
        """
        Create an archive from source files/directories
        
        Args:
            source_paths: List of paths to include in archive
            archive_path: Destination path for the archive
            format_type: Archive format ('tar', 'tar.gz', 'tar.bz2', 'tar.xz', 'zip')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._log(f"Creating {format_type} archive: {archive_path}")
            
            # Determine format info
            format_info = None
            for ext, info in self.SUPPORTED_FORMATS.items():
                if ext.lstrip('.') == format_type or ext == f'.{format_type}':
                    format_info = info
                    break
            
            if not format_info:
                self._log(f"Unsupported archive format: {format_type}", "ERROR")
                return False
            
            # Handle cross-storage scenarios
            source_schemes = {path.get_scheme() for path in source_paths}
            dest_scheme = archive_path.get_scheme()
            
            # If all sources and destination are local, create directly
            if all(scheme == 'file' for scheme in source_schemes) and dest_scheme == 'file':
                success = self._create_archive_local(source_paths, archive_path, format_info)
            else:
                # For cross-storage, use temporary file approach
                success = self._create_archive_cross_storage(source_paths, archive_path, format_info)
            
            # Invalidate cache for the archive creation if successful
            if success and self.cache_manager:
                self.cache_manager.invalidate_cache_for_archive_operation(archive_path, source_paths)
            
            return success
            
        except Exception as e:
            self._log(f"Error creating archive: {e}", "ERROR")
            return False
    
    def _create_archive_local(self, source_paths: List[Path], archive_path: Path, 
                             format_info: dict) -> bool:
        """Create archive when all paths are local"""
        try:
            if format_info['type'] == 'tar':
                mode = 'w'
                if format_info['compression'] == 'gz':
                    mode = 'w:gz'
                elif format_info['compression'] == 'bz2':
                    mode = 'w:bz2'
                elif format_info['compression'] == 'xz':
                    mode = 'w:xz'
                
                with tarfile.open(str(archive_path), mode) as tar:
                    for source_path in source_paths:
                        # Use relative path for archive member name
                        arcname = source_path.name
                        tar.add(str(source_path), arcname=arcname)
                        self._log(f"Added to archive: {arcname}")
            
            elif format_info['type'] == 'zip':
                with zipfile.ZipFile(str(archive_path), 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for source_path in source_paths:
                        if source_path.is_file():
                            zip_file.write(str(source_path), source_path.name)
                            self._log(f"Added to archive: {source_path.name}")
                        elif source_path.is_dir():
                            # Add directory recursively
                            for file_path in source_path.rglob('*'):
                                if file_path.is_file():
                                    # Create relative path within the directory
                                    rel_path = file_path.relative_to(source_path.parent)
                                    zip_file.write(str(file_path), str(rel_path))
                                    self._log(f"Added to archive: {rel_path}")
            
            else:
                self._log(f"Unsupported archive type for local creation: {format_info['type']}", "ERROR")
                return False
            
            self._log(f"Archive created successfully: {archive_path}")
            return True
            
        except Exception as e:
            self._log(f"Error creating local archive: {e}", "ERROR")
            return False
    
    def _create_archive_cross_storage(self, source_paths: List[Path], archive_path: Path, 
                                     format_info: dict) -> bool:
        """Create archive with cross-storage support using temporary files"""
        temp_dir = None
        temp_archive = None
        
        try:
            # Create temporary directory for staging
            temp_dir = tempfile.mkdtemp(prefix='tfm_archive_')
            temp_dir_path = PathlibPath(temp_dir)
            
            # Download/copy source files to temporary directory
            staged_paths = []
            for source_path in source_paths:
                if source_path.is_remote():
                    # Download remote file/directory to temp
                    temp_item = temp_dir_path / source_path.name
                    if source_path.is_file():
                        # Copy file content
                        temp_item.write_bytes(source_path.read_bytes())
                        staged_paths.append(Path(temp_item))
                        self._log(f"Downloaded to temp: {source_path.name}")
                    elif source_path.is_dir():
                        # Recursively download directory
                        temp_item.mkdir()
                        self._download_directory_recursive(source_path, Path(temp_item))
                        staged_paths.append(Path(temp_item))
                        self._log(f"Downloaded directory to temp: {source_path.name}")
                else:
                    # Local file, can reference directly
                    staged_paths.append(source_path)
            
            # Create archive in temporary location
            temp_archive = temp_dir_path / f"archive{self._get_extension_for_format(format_info)}"
            success = self._create_archive_local(staged_paths, Path(temp_archive), format_info)
            
            if not success:
                return False
            
            # Upload/move archive to final destination
            if archive_path.is_remote():
                # Upload to remote storage
                archive_path.write_bytes(temp_archive.read_bytes())
                self._log(f"Uploaded archive to: {archive_path}")
            else:
                # Move to local destination
                import shutil
                shutil.move(str(temp_archive), str(archive_path))
                self._log(f"Moved archive to: {archive_path}")
            
            return True
            
        except Exception as e:
            self._log(f"Error creating cross-storage archive: {e}", "ERROR")
            return False
        
        finally:
            # Clean up temporary directory
            if temp_dir and PathlibPath(temp_dir).exists():
                import shutil
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    self._log(f"Warning: Could not clean up temp directory: {e}", "WARNING")
    
    def _download_directory_recursive(self, remote_dir: Path, local_dir: Path):
        """Recursively download a remote directory to local storage"""
        try:
            for item in remote_dir.iterdir():
                local_item = local_dir / item.name
                if item.is_file():
                    local_item.write_bytes(item.read_bytes())
                elif item.is_dir():
                    local_item.mkdir()
                    self._download_directory_recursive(item, local_item)
        except Exception as e:
            self._log(f"Error downloading directory {remote_dir}: {e}", "ERROR")
            raise
    
    def _get_extension_for_format(self, format_info: dict) -> str:
        """Get file extension for format info"""
        if format_info['type'] == 'tar':
            if format_info['compression'] == 'gz':
                return '.tar.gz'
            elif format_info['compression'] == 'bz2':
                return '.tar.bz2'
            elif format_info['compression'] == 'xz':
                return '.tar.xz'
            else:
                return '.tar'
        elif format_info['type'] == 'zip':
            return '.zip'
        else:
            return '.archive'
    
    def extract_archive(self, archive_path: Path, destination_dir: Path, 
                       overwrite: bool = False) -> bool:
        """
        Extract an archive to a destination directory
        
        Args:
            archive_path: Path to the archive file
            destination_dir: Directory to extract to
            overwrite: Whether to overwrite existing files
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not archive_path.is_file():
                self._log(f"Archive file not found: {archive_path}", "ERROR")
                return False
            
            format_info = self.get_archive_format(archive_path.name)
            if not format_info:
                self._log(f"Unsupported archive format: {archive_path.name}", "ERROR")
                return False
            
            self._log(f"Extracting archive: {archive_path} to {destination_dir}")
            
            # Handle cross-storage scenarios
            archive_scheme = archive_path.get_scheme()
            dest_scheme = destination_dir.get_scheme()
            
            # If both are local, extract directly
            if archive_scheme == 'file' and dest_scheme == 'file':
                success = self._extract_archive_local(archive_path, destination_dir, format_info, overwrite)
            else:
                # For cross-storage, use temporary file approach
                success = self._extract_archive_cross_storage(archive_path, destination_dir, format_info, overwrite)
            
            # Invalidate cache for the extraction if successful
            if success and self.cache_manager:
                self.cache_manager.invalidate_cache_for_directory(destination_dir, "archive extraction")
            
            return success
            
        except Exception as e:
            self._log(f"Error extracting archive: {e}", "ERROR")
            return False
    
    def _extract_archive_local(self, archive_path: Path, destination_dir: Path, 
                              format_info: dict, overwrite: bool) -> bool:
        """Extract archive when both paths are local"""
        try:
            # Ensure destination directory exists
            destination_dir.mkdir(parents=True, exist_ok=True)
            
            if format_info['type'] == 'tar':
                mode = 'r'
                if format_info['compression'] == 'gz':
                    mode = 'r:gz'
                elif format_info['compression'] == 'bz2':
                    mode = 'r:bz2'
                elif format_info['compression'] == 'xz':
                    mode = 'r:xz'
                
                with tarfile.open(str(archive_path), mode) as tar:
                    members = tar.getmembers()
                    members_to_extract = []
                    
                    # Check for overwrite conflicts and filter members
                    if not overwrite:
                        for member in members:
                            dest_path = destination_dir / member.name
                            if dest_path.exists():
                                self._log(f"File exists, skipping: {member.name}", "WARNING")
                            else:
                                members_to_extract.append(member)
                    else:
                        members_to_extract = members
                    
                    # Extract only the allowed members
                    if members_to_extract:
                        if overwrite:
                            tar.extractall(str(destination_dir))
                        else:
                            # Extract individual members to avoid overwriting
                            for member in members_to_extract:
                                tar.extract(member, str(destination_dir))
                    
                    self._log(f"Extracted {len(members_to_extract)} items")
            
            elif format_info['type'] == 'zip':
                with zipfile.ZipFile(str(archive_path), 'r') as zip_file:
                    members_to_extract = zip_file.namelist()
                    
                    # Check for overwrite conflicts and filter members
                    if not overwrite:
                        filtered_members = []
                        for member in members_to_extract:
                            dest_path = destination_dir / member
                            if dest_path.exists():
                                self._log(f"File exists, skipping: {member}", "WARNING")
                            else:
                                filtered_members.append(member)
                        members_to_extract = filtered_members
                    
                    # Extract only the allowed members
                    if members_to_extract:
                        if overwrite:
                            zip_file.extractall(str(destination_dir))
                        else:
                            # Extract individual members to avoid overwriting
                            for member in members_to_extract:
                                zip_file.extract(member, str(destination_dir))
                    
                    self._log(f"Extracted {len(members_to_extract)} items")
            
            elif format_info['type'] in ['gzip', 'bzip2', 'xz']:
                # Single file compression
                output_name = archive_path.stem
                if archive_path.suffix in ['.gz', '.bz2', '.xz']:
                    output_name = archive_path.stem
                
                output_path = destination_dir / output_name
                
                if output_path.exists() and not overwrite:
                    self._log(f"File exists, not overwriting: {output_name}", "WARNING")
                    return False
                
                # Decompress single file
                if format_info['type'] == 'gzip':
                    with gzip.open(str(archive_path), 'rb') as f_in:
                        output_path.write_bytes(f_in.read())
                elif format_info['type'] == 'bzip2':
                    with bz2.open(str(archive_path), 'rb') as f_in:
                        output_path.write_bytes(f_in.read())
                elif format_info['type'] == 'xz':
                    with lzma.open(str(archive_path), 'rb') as f_in:
                        output_path.write_bytes(f_in.read())
                
                self._log(f"Decompressed to: {output_name}")
            
            else:
                self._log(f"Unsupported archive type for local extraction: {format_info['type']}", "ERROR")
                return False
            
            self._log(f"Archive extracted successfully to: {destination_dir}")
            return True
            
        except Exception as e:
            self._log(f"Error extracting local archive: {e}", "ERROR")
            return False
    
    def _extract_archive_cross_storage(self, archive_path: Path, destination_dir: Path, 
                                      format_info: dict, overwrite: bool) -> bool:
        """Extract archive with cross-storage support using temporary files"""
        temp_dir = None
        
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix='tfm_extract_')
            temp_dir_path = PathlibPath(temp_dir)
            
            # Download archive to temporary location if remote
            if archive_path.is_remote():
                temp_archive = temp_dir_path / archive_path.name
                temp_archive.write_bytes(archive_path.read_bytes())
                archive_to_extract = Path(temp_archive)
                self._log(f"Downloaded archive to temp: {archive_path.name}")
            else:
                archive_to_extract = archive_path
            
            # Extract to temporary directory
            temp_extract_dir = temp_dir_path / 'extracted'
            temp_extract_dir.mkdir()
            
            success = self._extract_archive_local(archive_to_extract, Path(temp_extract_dir), 
                                                format_info, overwrite=True)
            
            if not success:
                return False
            
            # Upload/move extracted files to final destination
            if destination_dir.is_remote():
                # Upload extracted files to remote storage
                self._upload_directory_recursive(Path(temp_extract_dir), destination_dir, overwrite)
                self._log(f"Uploaded extracted files to: {destination_dir}")
            else:
                # Move extracted files to local destination
                destination_dir.mkdir(parents=True, exist_ok=True)
                for item in temp_extract_dir.iterdir():
                    dest_item = destination_dir / item.name
                    if item.is_file():
                        if dest_item.exists() and not overwrite:
                            self._log(f"File exists, skipping: {item.name}", "WARNING")
                            continue
                        import shutil
                        shutil.copy2(str(item), str(dest_item))
                    elif item.is_dir():
                        if dest_item.exists() and not overwrite:
                            self._log(f"Directory exists, skipping: {item.name}", "WARNING")
                            continue
                        import shutil
                        shutil.copytree(str(item), str(dest_item))
                
                self._log(f"Moved extracted files to: {destination_dir}")
            
            return True
            
        except Exception as e:
            self._log(f"Error extracting cross-storage archive: {e}", "ERROR")
            return False
        
        finally:
            # Clean up temporary directory
            if temp_dir and PathlibPath(temp_dir).exists():
                import shutil
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    self._log(f"Warning: Could not clean up temp directory: {e}", "WARNING")
    
    def _upload_directory_recursive(self, local_dir: Path, remote_dir: Path, overwrite: bool):
        """Recursively upload a local directory to remote storage"""
        try:
            # Ensure remote directory exists
            if not remote_dir.exists():
                remote_dir.mkdir(parents=True, exist_ok=True)
            
            for item in local_dir.iterdir():
                remote_item = remote_dir / item.name
                if item.is_file():
                    if remote_item.exists() and not overwrite:
                        self._log(f"Remote file exists, skipping: {item.name}", "WARNING")
                        continue
                    remote_item.write_bytes(item.read_bytes())
                elif item.is_dir():
                    if not remote_item.exists():
                        remote_item.mkdir(parents=True, exist_ok=True)
                    self._upload_directory_recursive(item, remote_item, overwrite)
        except Exception as e:
            self._log(f"Error uploading directory {local_dir}: {e}", "ERROR")
            raise
    
    def list_archive_contents(self, archive_path: Path) -> List[Tuple[str, int, str]]:
        """
        List contents of an archive file
        
        Args:
            archive_path: Path to the archive file
            
        Returns:
            List of tuples (name, size, type) for each item in archive
        """
        try:
            if not archive_path.is_file():
                return []
            
            format_info = self.get_archive_format(archive_path.name)
            if not format_info:
                return []
            
            contents = []
            
            # Download archive to temp if remote
            if archive_path.is_remote():
                temp_dir = tempfile.mkdtemp(prefix='tfm_list_')
                try:
                    temp_archive = PathlibPath(temp_dir) / archive_path.name
                    temp_archive.write_bytes(archive_path.read_bytes())
                    archive_to_list = str(temp_archive)
                except Exception:
                    import shutil
                    shutil.rmtree(temp_dir)
                    return []
            else:
                archive_to_list = str(archive_path)
                temp_dir = None
            
            try:
                if format_info['type'] == 'tar':
                    mode = 'r'
                    if format_info['compression'] == 'gz':
                        mode = 'r:gz'
                    elif format_info['compression'] == 'bz2':
                        mode = 'r:bz2'
                    elif format_info['compression'] == 'xz':
                        mode = 'r:xz'
                    
                    with tarfile.open(archive_to_list, mode) as tar:
                        for member in tar.getmembers():
                            item_type = 'dir' if member.isdir() else 'file'
                            contents.append((member.name, member.size, item_type))
                
                elif format_info['type'] == 'zip':
                    with zipfile.ZipFile(archive_to_list, 'r') as zip_file:
                        for info in zip_file.infolist():
                            item_type = 'dir' if info.is_dir() else 'file'
                            contents.append((info.filename, info.file_size, item_type))
                
            finally:
                # Clean up temp file if used
                if temp_dir:
                    import shutil
                    shutil.rmtree(temp_dir)
            
            return contents
            
        except Exception as e:
            self._log(f"Error listing archive contents: {e}", "ERROR")
            return []


class ArchiveUI:
    """Handles archive-related UI operations for the file manager"""
    
    def __init__(self, file_manager, archive_operations):
        """Initialize archive UI with file manager and archive operations"""
        self.file_manager = file_manager
        self.archive_operations = archive_operations
        self.log_manager = file_manager.log_manager
        self.progress_manager = file_manager.progress_manager
        self.cache_manager = file_manager.cache_manager
        self.config = file_manager.config
    
    def enter_create_archive_mode(self):
        """Enter archive creation mode"""
        current_pane = self.file_manager.get_current_pane()
        
        # Check if there are files to archive
        files_to_archive = []
        
        if current_pane['selected_files']:
            # Archive selected files
            for file_path_str in current_pane['selected_files']:
                file_path = Path(file_path_str)
                if file_path.exists():
                    files_to_archive.append(file_path)
        else:
            # Archive current file if no files are selected
            if current_pane['files']:
                selected_file = current_pane['files'][current_pane['selected_index']]
                files_to_archive.append(selected_file)
        
        if not files_to_archive:
            print("No files to archive")
            return
        
        # Determine default filename for single file/directory
        default_filename = ""
        if len(files_to_archive) == 1:
            # Use basename of the single file/directory with a dot for extension
            basename = files_to_archive[0].stem if files_to_archive[0].is_file() else files_to_archive[0].name
            default_filename = f"{basename}."
        
        # Enter archive creation mode using general dialog with default filename
        self.file_manager.general_dialog.show_status_line_input(
            prompt="Archive filename: ",
            help_text="ESC:cancel Enter:create (.zip/.tar.gz/.tgz)",
            initial_text=default_filename,
            callback=self.on_create_archive_confirm,
            cancel_callback=self.on_create_archive_cancel
        )
        self.file_manager.needs_full_redraw = True
        
        # Log what we're about to archive
        if len(files_to_archive) == 1:
            print(f"Creating archive from: {files_to_archive[0].name}")
        else:
            print(f"Creating archive from {len(files_to_archive)} selected items")
        print("Enter archive filename (with .zip, .tar.gz, or .tgz extension):")
    
    def on_create_archive_confirm(self, archive_name):
        """Handle create archive confirmation"""
        if not archive_name.strip():
            print("Invalid archive name")
            self.file_manager.general_dialog.hide()
            self.file_manager.needs_full_redraw = True
            return
        
        current_pane = self.file_manager.get_current_pane()
        other_pane = self.file_manager.get_inactive_pane()
        
        # Get files to archive
        files_to_archive = []
        
        if current_pane['selected_files']:
            # Archive selected files
            for file_path_str in current_pane['selected_files']:
                file_path = Path(file_path_str)
                if file_path.exists():
                    files_to_archive.append(file_path)
        else:
            # Archive current file if no files are selected
            if current_pane['files']:
                selected_file = current_pane['files'][current_pane['selected_index']]
                files_to_archive.append(selected_file)
        
        if not files_to_archive:
            print("No files to archive")
            self.file_manager.general_dialog.hide()
            self.file_manager.needs_full_redraw = True
            return
        
        archive_filename = archive_name.strip()
        archive_path = other_pane['path'] / archive_filename
        
        # Check if archive already exists
        if archive_path.exists():
            print(f"Archive '{archive_filename}' already exists")
            self.file_manager.general_dialog.hide()
            self.file_manager.needs_full_redraw = True
            return
        
        try:
            # Determine archive format from filename
            format_type = self._get_archive_format_from_filename(archive_filename)
            
            if not format_type:
                print(f"Unsupported archive format. Supported: .zip, .tar.gz, .tar.bz2, .tar.xz, .tgz, .tbz2, .txz")
                self.file_manager.general_dialog.hide()
                self.file_manager.needs_full_redraw = True
                return
            
            # Start progress tracking
            total_files = self._count_files_recursively(files_to_archive)
            self.progress_manager.start_operation(
                OperationType.ARCHIVE_CREATE, 
                total_files, 
                f"Creating {format_type}: {archive_filename}",
                self._progress_callback
            )
            
            try:
                # Use the cross-storage archive operations
                success = self.archive_operations.create_archive(files_to_archive, archive_path, format_type)
                
                if success:
                    print(f"Created archive: {archive_filename}")
                    
                    # Refresh the other pane to show the new archive
                    self.file_manager.refresh_files(other_pane)
                    
                    # Try to select the new archive in the other pane
                    for i, file_path in enumerate(other_pane['files']):
                        if file_path.name == archive_filename:
                            other_pane['selected_index'] = i
                            self.file_manager.adjust_scroll_for_selection(other_pane)
                            break
                else:
                    print(f"Failed to create archive: {archive_filename}")
                    
            finally:
                self.progress_manager.finish_operation()
            
            self.file_manager.general_dialog.hide()
            self.file_manager.needs_full_redraw = True
            
        except Exception as e:
            print(f"Error creating archive: {e}")
            self.progress_manager.finish_operation()
            self.file_manager.general_dialog.hide()
            self.file_manager.needs_full_redraw = True
    
    def on_create_archive_cancel(self):
        """Handle create archive cancellation"""
        print("Archive creation cancelled")
        self.file_manager.general_dialog.hide()
        self.file_manager.needs_full_redraw = True
    
    def extract_selected_archive(self):
        """Extract the selected archive file to the other pane"""
        current_pane = self.file_manager.get_current_pane()
        other_pane = self.file_manager.get_inactive_pane()
        
        if not current_pane['files']:
            print("No files in current directory")
            return
        
        # Get the selected file
        selected_file = current_pane['files'][current_pane['selected_index']]
        
        if not selected_file.is_file():
            print("Selected item is not a file")
            return
        
        # Check if it's an archive file using the archive operations
        if not self.archive_operations.is_archive(selected_file):
            print(f"'{selected_file.name}' is not a supported archive format")
            print("Supported formats: .zip, .tar.gz, .tar.bz2, .tar.xz, .tgz, .tbz2, .txz, .gz, .bz2, .xz")
            return
        
        # Create extraction directory in the other pane
        # Use the base name of the archive (without extension) as directory name
        archive_basename = self.get_archive_basename(selected_file.name)
        extract_dir = other_pane['path'] / archive_basename
        
        # Check if extract confirmation is enabled
        if getattr(self.config, 'CONFIRM_EXTRACT_ARCHIVE', True):
            # Show confirmation dialog
            message = f"Extract '{selected_file.name}' to {other_pane['path']}?"
            
            def extract_callback(confirmed):
                if confirmed:
                    self._proceed_with_extraction(selected_file, extract_dir, other_pane, archive_basename)
                else:
                    print("Extraction cancelled")
            
            self.file_manager.show_confirmation(message, extract_callback)
        else:
            # Proceed with extraction without confirmation
            self._proceed_with_extraction(selected_file, extract_dir, other_pane, archive_basename)
    
    def _proceed_with_extraction(self, selected_file, extract_dir, other_pane, archive_basename):
        """Proceed with extraction using archive operations"""
        # Check if extraction directory already exists
        if extract_dir.exists():
            message = f"Directory '{archive_basename}' already exists."
            choices = [
                {"text": "Overwrite", "key": "o", "value": "overwrite"},
                {"text": "Rename", "key": "r", "value": "rename"},
                {"text": "Cancel", "key": "c", "value": "cancel"}
            ]
            
            def handle_conflict_choice(choice):
                if choice == "overwrite":
                    self.perform_extraction(selected_file, extract_dir, other_pane, overwrite=True)
                elif choice == "rename":
                    self._handle_extraction_rename(selected_file, other_pane, archive_basename)
                else:
                    print("Extraction cancelled")
            
            self.file_manager.show_dialog(message, choices, handle_conflict_choice)
        else:
            self.perform_extraction(selected_file, extract_dir, other_pane, overwrite=False)
    
    def perform_extraction(self, archive_file, extract_dir, other_pane, overwrite=False):
        """Perform extraction using cross-storage archive operations"""
        try:
            # Start progress tracking
            self.progress_manager.start_operation(
                OperationType.ARCHIVE_EXTRACT,
                1,  # We don't know the exact count beforehand
                f"Extracting: {archive_file.name}",
                self._progress_callback
            )
            
            try:
                # Use the cross-storage archive operations
                success = self.archive_operations.extract_archive(archive_file, extract_dir, overwrite)
                
                if success:
                    print(f"Archive extracted successfully to: {extract_dir}")
                    
                    # Refresh the other pane to show the extracted contents
                    self.file_manager.refresh_files(other_pane)
                    self.file_manager.needs_full_redraw = True
                else:
                    print(f"Failed to extract archive: {archive_file.name}")
                    
            finally:
                self.progress_manager.finish_operation()
            
        except Exception as e:
            print(f"Error extracting archive: {e}")
            self.progress_manager.finish_operation()
    
    def get_archive_basename(self, filename):
        """Get the base name of an archive file (without extension)"""
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.tar.gz'):
            return filename[:-7]  # Remove .tar.gz
        elif filename_lower.endswith('.tar.bz2'):
            return filename[:-8]  # Remove .tar.bz2
        elif filename_lower.endswith('.tar.xz'):
            return filename[:-7]  # Remove .tar.xz
        elif filename_lower.endswith('.tgz'):
            return filename[:-4]  # Remove .tgz
        elif filename_lower.endswith('.tbz2'):
            return filename[:-5]  # Remove .tbz2
        elif filename_lower.endswith('.txz'):
            return filename[:-4]  # Remove .txz
        elif filename_lower.endswith('.zip'):
            return filename[:-4]  # Remove .zip
        elif filename_lower.endswith('.tar'):
            return filename[:-4]  # Remove .tar
        elif filename_lower.endswith('.gz'):
            return filename[:-3]  # Remove .gz
        elif filename_lower.endswith('.bz2'):
            return filename[:-4]  # Remove .bz2
        elif filename_lower.endswith('.xz'):
            return filename[:-3]  # Remove .xz
        else:
            # Fallback - remove last extension
            return Path(filename).stem
    
    def _handle_extraction_rename(self, archive_file, other_pane, original_basename):
        """Handle rename operation for extraction conflict"""
        # Store context for the rename callback
        self.file_manager._extraction_rename_context = {
            'archive_file': archive_file,
            'other_pane': other_pane,
            'original_basename': original_basename
        }
        
        # Use the general dialog for input
        from tfm_general_purpose_dialog import DialogHelpers
        DialogHelpers.create_rename_dialog(
            self.file_manager.general_dialog,
            original_basename,
            original_basename
        )
        self.file_manager.general_dialog.callback = self._on_extraction_rename_confirm
        self.file_manager.general_dialog.cancel_callback = self._on_extraction_rename_cancel
        self.file_manager.needs_full_redraw = True
    
    def _on_extraction_rename_confirm(self, new_name):
        """Handle extraction rename confirmation"""
        if not new_name or new_name.strip() == "":
            print("Extraction cancelled: empty directory name")
            self.file_manager.general_dialog.hide()
            self.file_manager.needs_full_redraw = True
            return
        
        context = self.file_manager._extraction_rename_context
        archive_file = context['archive_file']
        other_pane = context['other_pane']
        original_basename = context['original_basename']
        new_name = new_name.strip()
        new_extract_dir = other_pane['path'] / new_name
        
        # Hide the dialog first
        self.file_manager.general_dialog.hide()
        self.file_manager.needs_full_redraw = True
        
        # Check if the new name also conflicts
        if new_extract_dir.exists():
            # Show conflict dialog again with the new name
            message = f"Directory '{new_name}' already exists."
            choices = [
                {"text": "Overwrite", "key": "o", "value": "overwrite"},
                {"text": "Rename", "key": "r", "value": "rename"},
                {"text": "Cancel", "key": "c", "value": "cancel"}
            ]
            
            def handle_rename_conflict(choice):
                if choice == "overwrite":
                    # Extract with the new name, overwriting
                    self.perform_extraction(archive_file, new_extract_dir, other_pane, overwrite=True)
                    print(f"Extracted to '{new_name}' (overwrote existing)")
                elif choice == "rename":
                    # Ask for another name
                    self._handle_extraction_rename(archive_file, other_pane, original_basename)
                else:
                    print("Extraction cancelled")
            
            self.file_manager.show_dialog(message, choices, handle_rename_conflict)
        else:
            # No conflict, proceed with extraction
            self.perform_extraction(archive_file, new_extract_dir, other_pane, overwrite=False)
            print(f"Extracted to '{new_name}'")
    
    def _on_extraction_rename_cancel(self):
        """Handle extraction rename cancellation"""
        print("Extraction cancelled")
        self.file_manager.general_dialog.hide()
        self.file_manager.needs_full_redraw = True
    
    def _get_archive_format_from_filename(self, filename):
        """Get archive format string for the archive operations"""
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.tar.gz') or filename_lower.endswith('.tgz'):
            return 'tar.gz'
        elif filename_lower.endswith('.tar.bz2') or filename_lower.endswith('.tbz2'):
            return 'tar.bz2'
        elif filename_lower.endswith('.tar.xz') or filename_lower.endswith('.txz'):
            return 'tar.xz'
        elif filename_lower.endswith('.tar'):
            return 'tar'
        elif filename_lower.endswith('.zip'):
            return 'zip'
        else:
            return None
    
    def _count_files_recursively(self, paths):
        """Count total number of individual files in the given paths (including files in directories)"""
        total_files = 0
        for path in paths:
            if path.is_file() or path.is_symlink():
                total_files += 1
            elif path.is_dir():
                try:
                    for root, dirs, files in os.walk(path):
                        total_files += len(files)
                        # Count symlinks to directories as files
                        for d in dirs:
                            dir_path = Path(root) / d
                            if dir_path.is_symlink():
                                total_files += 1
                except (PermissionError, OSError):
                    # If we can't walk the directory, count it as 1 item
                    total_files += 1
        return total_files
    
    def _progress_callback(self, progress_data):
        """Callback for progress manager updates"""
        # Force a screen refresh to show progress
        try:
            self.file_manager.draw_status()
            self.file_manager.stdscr.refresh()
        except Exception as e:
            print(f"Warning: Progress callback display update failed: {e}")
    
    # Legacy methods for backward compatibility
    def detect_archive_format(self, filename):
        """Detect archive format from filename extension (legacy method)"""
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.zip'):
            return 'zip'
        elif filename_lower.endswith('.tar.gz'):
            return 'tar.gz'
        elif filename_lower.endswith('.tgz'):
            return 'tgz'
        else:
            return None