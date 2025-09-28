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
from pathlib import Path as PathlibPath
from tfm_path import Path
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
    
    def __init__(self, log_manager=None, cache_manager=None):
        """Initialize archive operations with optional logging and cache management"""
        self.log_manager = log_manager
        self.cache_manager = cache_manager
    
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