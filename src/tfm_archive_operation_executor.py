#!/usr/bin/env python3
"""
TFM Archive Operation Executor - Handles archive I/O operations in background threads
"""

import os
import tempfile
import tarfile
import zipfile
import threading
from pathlib import Path as PathlibPath
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass

from tfm_path import Path
from tfm_progress_manager import ProgressManager, OperationType
from tfm_log_manager import getLogger
from tfm_archive import ArchiveError


@dataclass
class ArchiveFormatInfo:
    """Information about an archive format"""
    type: str  # 'tar', 'zip', 'gzip', 'bzip2', 'xz'
    compression: Optional[str] = None  # 'gz', 'bz2', 'xz', or None
    extension: str = ''


@dataclass
class ConflictInfo:
    """Information about a detected conflict.
    
    Used to pass conflict details to UI for display.
    
    Attributes:
        conflict_type: Type of conflict ('archive_exists' or 'file_exists')
        path: Conflicting path
        size: File size if applicable (None for directories or non-existent files)
        is_directory: Whether conflict is a directory
    """
    conflict_type: str
    path: Path
    size: Optional[int] = None
    is_directory: bool = False


class ArchiveOperationExecutor:
    """
    Executor for archive operations with background thread support.
    
    This class handles the actual I/O operations for archive creation and extraction,
    running them in background threads to keep the UI responsive. It integrates with
    ProgressManager for progress tracking and supports operation cancellation.
    
    Migrated from ArchiveOperations class with threading and progress tracking added.
    """
    
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
    }

    def __init__(self, file_manager, progress_manager: ProgressManager, cache_manager=None):
        """
        Initialize the archive operation executor.
        
        Args:
            file_manager: Reference to the file manager for accessing operation flags
            progress_manager: Progress manager for tracking operation progress
            cache_manager: Optional cache manager for cache invalidation
        """
        self.file_manager = file_manager
        self.progress_manager = progress_manager
        self.cache_manager = cache_manager
        self.logger = getLogger("ArchiveExec")
        
        # Thread tracking
        self._current_thread: Optional[threading.Thread] = None
    
    def is_archive(self, path: Path) -> bool:
        """
        Check if a file is a supported archive format.
        
        Args:
            path: Path to check
            
        Returns:
            True if file is a supported archive format
        """
        if not path.is_file():
            return False
        
        return self._get_archive_format(path.name) is not None
    
    def perform_create_operation(self, source_paths: List[Path], archive_path: Path,
                                format_type: str, completion_callback: Optional[Callable] = None):
        """
        Create archive in background thread with progress tracking.
        
        Migrated from ArchiveOperations.create_archive() with threading support.
        
        Args:
            source_paths: List of paths to include in archive
            archive_path: Destination path for the archive
            format_type: Archive format ('tar', 'tar.gz', 'tar.bz2', 'tar.xz', 'zip')
            completion_callback: Optional callback(success_count, error_count) on completion
        """
        # Create and start background thread
        thread = threading.Thread(
            target=self._create_archive_thread,
            args=(source_paths, archive_path, format_type, completion_callback),
            daemon=True
        )
        self._current_thread = thread
        thread.start()
    
    def perform_extract_operation(self, archive_path: Path, destination_dir: Path,
                                 overwrite: bool, skip_files: List[str] = None,
                                 completion_callback: Optional[Callable] = None):
        """
        Extract archive in background thread with progress tracking.
        
        Migrated from ArchiveOperations.extract_archive() with threading support.
        
        Args:
            archive_path: Path to the archive file
            destination_dir: Directory to extract to
            overwrite: Whether to overwrite existing files
            skip_files: List of filenames to skip during extraction (optional)
            completion_callback: Optional callback(success_count, error_count) on completion
        """
        # Create and start background thread
        thread = threading.Thread(
            target=self._extract_archive_thread,
            args=(archive_path, destination_dir, overwrite, skip_files or [], completion_callback),
            daemon=True
        )
        self._current_thread = thread
        thread.start()

    def _create_archive_thread(self, source_paths: List[Path], archive_path: Path,
                              format_type: str, completion_callback: Optional[Callable]):
        """Background thread for archive creation"""
        success_count = 0
        error_count = 0
        
        try:
            self.logger.info(f"Creating {format_type} archive: {archive_path}")
            
            # Determine format info
            format_info = self._get_format_info(format_type)
            if not format_info:
                self.logger.error(f"Unsupported archive format: {format_type}")
                error_count += 1
                if completion_callback:
                    completion_callback(success_count, error_count)
                return
            
            # Start progress tracking with unknown total (use 0 for unknown total)
            # Progress will update as files are added
            self.progress_manager.start_operation(
                OperationType.ARCHIVE_CREATE,
                0,  # Unknown total - will show count instead of percentage
                f"Creating {archive_path.name}",
                self._progress_callback
            )
            
            # Start animation refresh loop
            import time
            stop_animation = threading.Event()
            animation_thread = threading.Thread(
                target=self._animation_refresh_loop,
                args=(stop_animation,),
                daemon=True
            )
            animation_thread.start()
            
            try:
                # Handle cross-storage scenarios
                source_schemes = {path.get_scheme() for path in source_paths}
                dest_scheme = archive_path.get_scheme()
                
                # If all sources and destination are local, create directly
                if all(scheme == 'file' for scheme in source_schemes) and dest_scheme == 'file':
                    success_count, error_count = self._create_archive_local(
                        source_paths, archive_path, format_info, completion_callback
                    )
                else:
                    # For cross-storage, use temporary file approach
                    success_count, error_count = self._create_archive_cross_storage(
                        source_paths, archive_path, format_info
                    )
            finally:
                # Stop animation loop
                stop_animation.set()
                animation_thread.join(timeout=0.5)
            
            # Finish progress tracking
            self.progress_manager.finish_operation()
            
            # Invalidate cache if successful and not cancelled
            if success_count > 0 and self.cache_manager:
                if not (hasattr(self.file_manager, 'operation_cancelled') and self.file_manager.operation_cancelled):
                    self.cache_manager.invalidate_cache_for_archive_operation(archive_path, source_paths)
            
        except Exception as e:
            self.logger.error(f"Error creating archive: {e}")
            error_count += 1
            self.progress_manager.increment_errors()
            self.progress_manager.finish_operation()
        
        finally:
            # Always invoke completion callback, even if cancelled
            if completion_callback:
                completion_callback(success_count, error_count)

    def _extract_archive_thread(self, archive_path: Path, destination_dir: Path,
                               overwrite: bool, skip_files: List[str],
                               completion_callback: Optional[Callable]):
        """Background thread for archive extraction"""
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        try:
            if not archive_path.is_file():
                self.logger.error(f"Archive file not found: {archive_path}")
                error_count += 1
                if completion_callback:
                    completion_callback(success_count, error_count)
                return
            
            format_info = self._get_archive_format(archive_path.name)
            if not format_info:
                self.logger.error(f"Unsupported archive format: {archive_path.name}")
                error_count += 1
                if completion_callback:
                    completion_callback(success_count, error_count)
                return
            
            self.logger.info(f"Extracting archive: {archive_path} to {destination_dir}")
            
            # Start progress tracking with unknown total (use 0 for unknown total)
            # Progress will update as files are extracted
            self.progress_manager.start_operation(
                OperationType.ARCHIVE_EXTRACT,
                0,  # Unknown total - will show count instead of percentage
                f"Extracting {archive_path.name}",
                self._progress_callback
            )
            
            # Start animation refresh loop
            import time
            stop_animation = threading.Event()
            animation_thread = threading.Thread(
                target=self._animation_refresh_loop,
                args=(stop_animation,),
                daemon=True
            )
            animation_thread.start()
            
            try:
                # Handle cross-storage scenarios
                archive_scheme = archive_path.get_scheme()
                dest_scheme = destination_dir.get_scheme()
                
                # If both are local, extract directly
                if archive_scheme == 'file' and dest_scheme == 'file':
                    success_count, error_count, skipped_count = self._extract_archive_local(
                        archive_path, destination_dir, format_info, overwrite, skip_files, completion_callback
                    )
                else:
                    # For cross-storage, use temporary file approach
                    success_count, error_count, skipped_count = self._extract_archive_cross_storage(
                        archive_path, destination_dir, format_info, overwrite, skip_files
                    )
            finally:
                # Stop animation loop
                stop_animation.set()
                animation_thread.join(timeout=0.5)
            
            # Finish progress tracking
            self.progress_manager.finish_operation()
            
            # Invalidate cache if successful and not cancelled
            if success_count > 0 and self.cache_manager:
                if not (hasattr(self.file_manager, 'operation_cancelled') and self.file_manager.operation_cancelled):
                    self.cache_manager.invalidate_cache_for_directory(destination_dir, "archive extraction")
            
        except Exception as e:
            self.logger.error(f"Error extracting archive: {e}")
            error_count += 1
            self.progress_manager.increment_errors()
            self.progress_manager.finish_operation()
        
        finally:
            # Always invoke completion callback, even if cancelled
            if completion_callback:
                completion_callback(success_count, error_count)

    def _count_files_recursively(self, paths: List[Path]) -> int:
        """
        Count total files for progress tracking.
        
        Args:
            paths: List of paths to count
            
        Returns:
            Total number of files
        """
        total = 0
        for path in paths:
            # Check for cancellation
            if hasattr(self.file_manager, 'operation_cancelled') and self.file_manager.operation_cancelled:
                break
            
            try:
                if path.is_file():
                    total += 1
                elif path.is_dir():
                    # Count files in directory recursively
                    for item in path.rglob('*'):
                        if hasattr(self.file_manager, 'operation_cancelled') and self.file_manager.operation_cancelled:
                            break
                        if item.is_file():
                            total += 1
            except Exception as e:
                self.logger.error(f"Error counting files in {path}: {e}")
        
        return total
    
    def _count_archive_files(self, archive_path: Path, format_info: Dict) -> int:
        """
        Count files in archive for progress tracking.
        
        Args:
            archive_path: Path to archive file
            format_info: Archive format information
            
        Returns:
            Number of files in archive
        """
        try:
            # Download archive to temp if remote
            if archive_path.is_remote():
                temp_dir = tempfile.mkdtemp(prefix='tfm_count_')
                try:
                    temp_archive = PathlibPath(temp_dir) / archive_path.name
                    temp_archive.write_bytes(archive_path.read_bytes())
                    archive_to_count = str(temp_archive)
                except Exception:
                    import shutil
                    shutil.rmtree(temp_dir)
                    return 0
            else:
                archive_to_count = str(archive_path)
                temp_dir = None
            
            count = 0
            try:
                if format_info['type'] == 'tar':
                    mode = self._get_tar_mode(format_info, 'r')
                    with tarfile.open(archive_to_count, mode) as tar:
                        count = len([m for m in tar.getmembers() if m.isfile()])
                elif format_info['type'] == 'zip':
                    with zipfile.ZipFile(archive_to_count, 'r') as zip_file:
                        count = len([i for i in zip_file.infolist() if not i.is_dir()])
            finally:
                if temp_dir:
                    import shutil
                    shutil.rmtree(temp_dir)
            
            return count
        except Exception as e:
            self.logger.error(f"Error counting archive files: {e}")
            return 0
    
    def _progress_callback(self, operation=None):
        """Callback for progress manager to trigger UI refresh"""
        if hasattr(self.file_manager, 'mark_dirty'):
            self.file_manager.mark_dirty()
    
    def _animation_refresh_loop(self, stop_event):
        """Background loop to refresh animation periodically
        
        Args:
            stop_event: Threading event to signal when to stop
        """
        import time
        
        while not stop_event.is_set():
            # Refresh animation to keep spinner moving
            self.progress_manager.refresh_animation()
            
            # Sleep for a short time (100ms) to keep animation smooth
            # This is independent of progress updates
            time.sleep(0.1)
    
    def _check_conflicts(self, operation_type: str, source_paths: List[Path], 
                        destination: Path) -> List[ConflictInfo]:
        """
        Check for file conflicts before executing archive operation.
        
        For create operations: checks if destination archive file already exists
        For extract operations: checks if any files in archive would overwrite existing files
        
        Args:
            operation_type: Type of operation ('create' or 'extract')
            source_paths: List of source paths (files to archive or archive file to extract)
            destination: Destination path (archive file or extraction directory)
            
        Returns:
            List of ConflictInfo objects describing detected conflicts
        """
        conflicts = []
        
        try:
            if operation_type == 'create':
                # Check if destination archive file already exists
                if destination.exists():
                    conflict = ConflictInfo(
                        conflict_type='archive_exists',
                        path=destination,
                        size=destination.stat().st_size if destination.is_file() else None,
                        is_directory=destination.is_dir()
                    )
                    conflicts.append(conflict)
                    self.logger.info(f"Conflict detected: archive file {destination.name} already exists")
            
            elif operation_type == 'extract':
                # Check if any files in archive would overwrite existing files
                # We need to get the archive format and list its contents
                if not source_paths or not source_paths[0].is_file():
                    self.logger.error("Extract operation requires valid archive file")
                    return conflicts
                
                archive_path = source_paths[0]
                format_info = self._get_archive_format(archive_path.name)
                
                if not format_info:
                    self.logger.error(f"Unsupported archive format: {archive_path.name}")
                    return conflicts
                
                # Get list of files in archive that would conflict
                conflicting_files = self._get_conflicting_files_in_archive(
                    archive_path, destination, format_info
                )
                
                for file_path in conflicting_files:
                    # Check for cancellation during conflict detection
                    if hasattr(self.file_manager, 'operation_cancelled') and self.file_manager.operation_cancelled:
                        self.logger.info("Conflict detection cancelled")
                        break
                    
                    conflict = ConflictInfo(
                        conflict_type='file_exists',
                        path=file_path,
                        size=file_path.stat().st_size if file_path.exists() and file_path.is_file() else None,
                        is_directory=file_path.is_dir() if file_path.exists() else False
                    )
                    conflicts.append(conflict)
                
                if conflicts:
                    self.logger.info(f"Conflict detected: {len(conflicts)} file(s) would be overwritten")
        
        except Exception as e:
            self.logger.error(f"Error checking conflicts: {e}")
        
        return conflicts
    
    def _get_conflicting_files_in_archive(self, archive_path: Path, destination_dir: Path,
                                         format_info: Dict) -> List[Path]:
        """
        Get list of files in archive that would conflict with existing files.
        
        Args:
            archive_path: Path to archive file
            destination_dir: Destination directory for extraction
            format_info: Archive format information
            
        Returns:
            List of Path objects that would conflict
        """
        conflicting_files = []
        
        try:
            # Download archive to temp if remote
            if archive_path.is_remote():
                temp_dir = tempfile.mkdtemp(prefix='tfm_conflict_')
                try:
                    temp_archive = PathlibPath(temp_dir) / archive_path.name
                    temp_archive.write_bytes(archive_path.read_bytes())
                    archive_to_check = str(temp_archive)
                except Exception:
                    import shutil
                    shutil.rmtree(temp_dir)
                    return conflicting_files
            else:
                archive_to_check = str(archive_path)
                temp_dir = None
            
            try:
                if format_info['type'] == 'tar':
                    mode = self._get_tar_mode(format_info, 'r')
                    with tarfile.open(archive_to_check, mode) as tar:
                        for member in tar.getmembers():
                            # Check for cancellation
                            if hasattr(self.file_manager, 'operation_cancelled') and self.file_manager.operation_cancelled:
                                break
                            
                            # Skip directories
                            if member.isdir():
                                continue
                            
                            # Check if file would conflict
                            dest_path = destination_dir / member.name
                            if dest_path.exists():
                                conflicting_files.append(dest_path)
                
                elif format_info['type'] == 'zip':
                    with zipfile.ZipFile(archive_to_check, 'r') as zip_file:
                        for member in zip_file.namelist():
                            # Check for cancellation
                            if hasattr(self.file_manager, 'operation_cancelled') and self.file_manager.operation_cancelled:
                                break
                            
                            # Skip directories
                            if member.endswith('/'):
                                continue
                            
                            # Check if file would conflict
                            dest_path = destination_dir / member
                            if dest_path.exists():
                                conflicting_files.append(dest_path)
            
            finally:
                if temp_dir:
                    import shutil
                    shutil.rmtree(temp_dir)
        
        except Exception as e:
            self.logger.error(f"Error getting conflicting files: {e}")
        
        return conflicting_files

    def _get_format_info(self, format_type: str) -> Optional[Dict]:
        """
        Get format information for the given format type.
        
        Args:
            format_type: Format type string (e.g., 'tar.gz', 'zip')
            
        Returns:
            Format info dict or None if unsupported
        """
        for ext, info in self.SUPPORTED_FORMATS.items():
            if ext.lstrip('.') == format_type or ext == f'.{format_type}':
                return info
        return None
    
    def _get_archive_format(self, filename: str) -> Optional[Dict]:
        """
        Get archive format based on file extension.
        
        Migrated from ArchiveOperations._get_archive_handler() logic.
        
        Args:
            filename: Archive filename
            
        Returns:
            Format info dict or None if unsupported
        """
        filename_lower = filename.lower()
        
        # Check for multi-part extensions first (e.g., .tar.gz)
        for ext in ['.tar.gz', '.tar.bz2', '.tar.xz', '.tgz', '.tbz2', '.txz']:
            if filename_lower.endswith(ext):
                return self.SUPPORTED_FORMATS[ext]
        
        # Check for single extensions
        for ext in ['.tar', '.zip']:
            if filename_lower.endswith(ext):
                return self.SUPPORTED_FORMATS[ext]
        
        return None
    
    def _get_tar_mode(self, format_info: Dict, operation: str) -> str:
        """
        Get tarfile mode string based on format info.
        
        Args:
            format_info: Format information dict
            operation: 'r' for read, 'w' for write
            
        Returns:
            Mode string for tarfile.open()
        """
        if format_info['compression'] == 'gz':
            return f'{operation}:gz'
        elif format_info['compression'] == 'bz2':
            return f'{operation}:bz2'
        elif format_info['compression'] == 'xz':
            return f'{operation}:xz'
        else:
            return operation
    
    def _get_extension_for_format(self, format_info: Dict) -> str:
        """
        Get file extension for format info.
        
        Args:
            format_info: Format information dict
            
        Returns:
            File extension string
        """
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

    def _create_archive_local(self, source_paths: List[Path], archive_path: Path,
                             format_info: Dict, completion_callback: Optional[Callable] = None) -> tuple:
        """
        Create archive when all paths are local.
        
        Migrated from ArchiveOperations._create_archive_local().
        
        Args:
            source_paths: List of source paths
            archive_path: Destination archive path
            format_info: Archive format information
            
        Returns:
            Tuple of (success_count, error_count)
        """
        success_count = 0
        error_count = 0
        archive_created = False
        
        try:
            if format_info['type'] == 'tar':
                mode = self._get_tar_mode(format_info, 'w')
                
                with tarfile.open(str(archive_path), mode) as tar:
                    archive_created = True
                    for source_path in source_paths:
                        # Check for cancellation
                        if hasattr(self.file_manager, 'operation_cancelled') and self.file_manager.operation_cancelled:
                            self.logger.info("Archive creation cancelled")
                            break
                        
                        try:
                            if source_path.is_file():
                                # Update progress before adding file
                                success_count += 1
                                self.progress_manager.update_progress(source_path.name, success_count)
                                
                                # Add single file
                                tar.add(str(source_path), arcname=source_path.name)
                                self.logger.info(f"Added to archive: {source_path.name}")
                            elif source_path.is_dir():
                                # Update progress immediately to show we're processing this directory
                                success_count += 1
                                self.progress_manager.update_progress(f"{source_path.name}/", success_count)
                                
                                # Add directory recursively with progress updates per file
                                for file_path in source_path.rglob('*'):
                                    # Check for cancellation
                                    if hasattr(self.file_manager, 'operation_cancelled') and self.file_manager.operation_cancelled:
                                        break
                                    
                                    if file_path.is_file():
                                        try:
                                            # Create relative path within the directory
                                            rel_path = file_path.relative_to(source_path.parent)
                                            
                                            # Update progress before adding file
                                            success_count += 1
                                            self.progress_manager.update_progress(str(rel_path), success_count)
                                            
                                            # Add file to archive
                                            tar.add(str(file_path), arcname=str(rel_path))
                                            self.logger.info(f"Added to archive: {rel_path}")
                                        except PermissionError as e:
                                            self.logger.error(f"Permission denied adding {file_path.name} to archive: {e}")
                                            error_count += 1
                                            self.progress_manager.increment_errors()
                                            # Continue with next file
                                        except OSError as e:
                                            # Check for disk space exhaustion
                                            if "No space left" in str(e) or "Disk quota exceeded" in str(e):
                                                self.logger.error(f"Disk space exhausted during archive creation: {e}")
                                                error_count += 1
                                                self.progress_manager.increment_errors()
                                                # Stop operation - cannot continue
                                                break
                                            else:
                                                self.logger.error(f"OS error adding {file_path.name} to archive: {e}")
                                                error_count += 1
                                                self.progress_manager.increment_errors()
                                                # Continue with next file
                                        except ArchiveError as e:
                                            self.logger.error(f"Archive error adding {file_path.name}: {e.user_message if hasattr(e, 'user_message') and e.user_message else str(e)}")
                                            error_count += 1
                                            self.progress_manager.increment_errors()
                                            # Continue with next file
                                        except Exception as e:
                                            self.logger.error(f"Unexpected error adding {file_path.name} to archive: {e}")
                                            error_count += 1
                                            self.progress_manager.increment_errors()
                                            # Continue with next file
                        except PermissionError as e:
                            self.logger.error(f"Permission denied adding {source_path.name} to archive: {e}")
                            error_count += 1
                            self.progress_manager.increment_errors()
                            # Continue with next file
                        except OSError as e:
                            # Check for disk space exhaustion
                            if "No space left" in str(e) or "Disk quota exceeded" in str(e):
                                self.logger.error(f"Disk space exhausted during archive creation: {e}")
                                error_count += 1
                                self.progress_manager.increment_errors()
                                # Stop operation - cannot continue
                                break
                            else:
                                self.logger.error(f"OS error adding {source_path.name} to archive: {e}")
                                error_count += 1
                                self.progress_manager.increment_errors()
                                # Continue with next file
                        except ArchiveError as e:
                            self.logger.error(f"Archive error adding {source_path.name}: {e.user_message if hasattr(e, 'user_message') and e.user_message else str(e)}")
                            error_count += 1
                            self.progress_manager.increment_errors()
                            # Continue with next file
                        except Exception as e:
                            self.logger.error(f"Unexpected error adding {source_path.name} to archive: {e}")
                            error_count += 1
                            self.progress_manager.increment_errors()
                            # Continue with next file
            
            elif format_info['type'] == 'zip':
                with zipfile.ZipFile(str(archive_path), 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    archive_created = True
                    for source_path in source_paths:
                        # Check for cancellation
                        if hasattr(self.file_manager, 'operation_cancelled') and self.file_manager.operation_cancelled:
                            self.logger.info("Archive creation cancelled")
                            break
                        
                        try:
                            if source_path.is_file():
                                # Update progress before writing
                                success_count += 1
                                self.progress_manager.update_progress(source_path.name, success_count)
                                zip_file.write(str(source_path), source_path.name)
                                self.logger.info(f"Added to archive: {source_path.name}")
                            elif source_path.is_dir():
                                # Update progress immediately to show we're processing this directory
                                success_count += 1
                                self.progress_manager.update_progress(f"{source_path.name}/", success_count)
                                
                                # Add directory recursively
                                for file_path in source_path.rglob('*'):
                                    # Check for cancellation
                                    if hasattr(self.file_manager, 'operation_cancelled') and self.file_manager.operation_cancelled:
                                        break
                                    
                                    if file_path.is_file():
                                        try:
                                            # Create relative path within the directory
                                            rel_path = file_path.relative_to(source_path.parent)
                                            
                                            # Update progress before writing
                                            success_count += 1
                                            self.progress_manager.update_progress(str(rel_path), success_count)
                                            
                                            zip_file.write(str(file_path), str(rel_path))
                                            self.logger.info(f"Added to archive: {rel_path}")
                                        except PermissionError as e:
                                            self.logger.error(f"Permission denied adding {file_path.name} to archive: {e}")
                                            error_count += 1
                                            self.progress_manager.increment_errors()
                                            # Continue with next file
                                        except OSError as e:
                                            # Check for disk space exhaustion
                                            if "No space left" in str(e) or "Disk quota exceeded" in str(e):
                                                self.logger.error(f"Disk space exhausted during archive creation: {e}")
                                                error_count += 1
                                                self.progress_manager.increment_errors()
                                                # Stop operation - cannot continue
                                                break
                                            else:
                                                self.logger.error(f"OS error adding {file_path.name} to archive: {e}")
                                                error_count += 1
                                                self.progress_manager.increment_errors()
                                                # Continue with next file
                                        except ArchiveError as e:
                                            self.logger.error(f"Archive error adding {file_path.name}: {e.user_message if hasattr(e, 'user_message') and e.user_message else str(e)}")
                                            error_count += 1
                                            self.progress_manager.increment_errors()
                                            # Continue with next file
                                        except Exception as e:
                                            self.logger.error(f"Unexpected error adding {file_path.name} to archive: {e}")
                                            error_count += 1
                                            self.progress_manager.increment_errors()
                                            # Continue with next file
                        except PermissionError as e:
                            self.logger.error(f"Permission denied adding {source_path.name} to archive: {e}")
                            error_count += 1
                            self.progress_manager.increment_errors()
                            # Continue with next file
                        except OSError as e:
                            # Check for disk space exhaustion
                            if "No space left" in str(e) or "Disk quota exceeded" in str(e):
                                self.logger.error(f"Disk space exhausted during archive creation: {e}")
                                error_count += 1
                                self.progress_manager.increment_errors()
                                # Stop operation - cannot continue
                                break
                            else:
                                self.logger.error(f"OS error adding {source_path.name} to archive: {e}")
                                error_count += 1
                                self.progress_manager.increment_errors()
                                # Continue with next file
                        except ArchiveError as e:
                            self.logger.error(f"Archive error adding {source_path.name}: {e.user_message if hasattr(e, 'user_message') and e.user_message else str(e)}")
                            error_count += 1
                            self.progress_manager.increment_errors()
                            # Continue with next file
                        except Exception as e:
                            self.logger.error(f"Unexpected error adding {source_path.name} to archive: {e}")
                            error_count += 1
                            self.progress_manager.increment_errors()
                            # Continue with next file
            
            else:
                self.logger.error(f"Unsupported archive type for local creation: {format_info['type']}")
                error_count += 1
                self.progress_manager.increment_errors()
                return (success_count, error_count)
            
            # Check if operation was cancelled
            was_cancelled = hasattr(self.file_manager, 'operation_cancelled') and self.file_manager.operation_cancelled
            
            if was_cancelled and archive_created:
                # Clean up partial archive file
                try:
                    if archive_path.exists():
                        archive_path.unlink()
                        self.logger.info(f"Removed partial archive file: {archive_path.name}")
                except Exception as e:
                    self.logger.warning(f"Could not remove partial archive: {e}")
            elif success_count > 0 and not completion_callback:
                # Only log summary if no callback provided (callback suppresses default logging)
                self.logger.info(f"Archive created successfully: {archive_path}")
            
        except PermissionError as e:
            self.logger.error(f"Permission denied creating archive {archive_path.name}: {e}")
            error_count += 1
            self.progress_manager.increment_errors()
            
            # Clean up partial archive on error
            if archive_created:
                try:
                    if archive_path.exists():
                        archive_path.unlink()
                        self.logger.info(f"Removed partial archive file after error: {archive_path.name}")
                except Exception as cleanup_error:
                    self.logger.warning(f"Could not remove partial archive: {cleanup_error}")
        except OSError as e:
            # Check for disk space exhaustion
            if "No space left" in str(e) or "Disk quota exceeded" in str(e):
                self.logger.error(f"Disk space exhausted creating archive {archive_path.name}: {e}")
            else:
                self.logger.error(f"OS error creating archive {archive_path.name}: {e}")
            error_count += 1
            self.progress_manager.increment_errors()
            
            # Clean up partial archive on error
            if archive_created:
                try:
                    if archive_path.exists():
                        archive_path.unlink()
                        self.logger.info(f"Removed partial archive file after error: {archive_path.name}")
                except Exception as cleanup_error:
                    self.logger.warning(f"Could not remove partial archive: {cleanup_error}")
        except ArchiveError as e:
            self.logger.error(f"Archive error creating {archive_path.name}: {e.user_message if hasattr(e, 'user_message') and e.user_message else str(e)}")
            error_count += 1
            self.progress_manager.increment_errors()
            
            # Clean up partial archive on error
            if archive_created:
                try:
                    if archive_path.exists():
                        archive_path.unlink()
                        self.logger.info(f"Removed partial archive file after error: {archive_path.name}")
                except Exception as cleanup_error:
                    self.logger.warning(f"Could not remove partial archive: {cleanup_error}")
        except Exception as e:
            self.logger.error(f"Unexpected error creating local archive {archive_path.name}: {e}")
            error_count += 1
            self.progress_manager.increment_errors()
            
            # Clean up partial archive on error
            if archive_created:
                try:
                    if archive_path.exists():
                        archive_path.unlink()
                        self.logger.info(f"Removed partial archive file after error: {archive_path.name}")
                except Exception as cleanup_error:
                    self.logger.warning(f"Could not remove partial archive: {cleanup_error}")
        
        return (success_count, error_count)

    def _create_archive_cross_storage(self, source_paths: List[Path], archive_path: Path,
                                     format_info: Dict) -> tuple:
        """
        Create archive with cross-storage support using temporary files.
        
        Migrated from ArchiveOperations._create_archive_cross_storage().
        
        Args:
            source_paths: List of source paths
            archive_path: Destination archive path
            format_info: Archive format information
            
        Returns:
            Tuple of (success_count, error_count)
        """
        temp_dir = None
        temp_archive = None
        success_count = 0
        error_count = 0
        
        try:
            # Create temporary directory for staging
            temp_dir = tempfile.mkdtemp(prefix='tfm_archive_')
            temp_dir_path = PathlibPath(temp_dir)
            
            # Download/copy source files to temporary directory
            staged_paths = []
            for source_path in source_paths:
                # Check for cancellation
                if hasattr(self.file_manager, 'operation_cancelled') and self.file_manager.operation_cancelled:
                    self.logger.info("Archive creation cancelled")
                    break
                
                try:
                    if source_path.is_remote():
                        # Download remote file/directory to temp
                        temp_item = temp_dir_path / source_path.name
                        if source_path.is_file():
                            # Copy file content
                            temp_item.write_bytes(source_path.read_bytes())
                            staged_paths.append(Path(temp_item))
                            self.logger.info(f"Downloaded to temp: {source_path.name}")
                        elif source_path.is_dir():
                            # Recursively download directory
                            temp_item.mkdir()
                            self._download_directory_recursive(source_path, Path(temp_item))
                            staged_paths.append(Path(temp_item))
                            self.logger.info(f"Downloaded directory to temp: {source_path.name}")
                    else:
                        # Local file, can reference directly
                        staged_paths.append(source_path)
                except PermissionError as e:
                    self.logger.error(f"Permission denied staging {source_path.name}: {e}")
                    error_count += 1
                    self.progress_manager.increment_errors()
                    # Continue with next file
                except OSError as e:
                    # Check for disk space exhaustion
                    if "No space left" in str(e) or "Disk quota exceeded" in str(e):
                        self.logger.error(f"Disk space exhausted staging files: {e}")
                        error_count += 1
                        self.progress_manager.increment_errors()
                        # Stop operation - cannot continue
                        break
                    else:
                        self.logger.error(f"OS error staging {source_path.name}: {e}")
                        error_count += 1
                        self.progress_manager.increment_errors()
                        # Continue with next file
                except ArchiveError as e:
                    self.logger.error(f"Archive error staging {source_path.name}: {e.user_message if hasattr(e, 'user_message') and e.user_message else str(e)}")
                    error_count += 1
                    self.progress_manager.increment_errors()
                    # Continue with next file
                except Exception as e:
                    self.logger.error(f"Unexpected error staging {source_path.name}: {e}")
                    error_count += 1
                    self.progress_manager.increment_errors()
                    # Continue with next file
            
            # Create archive in temporary location
            temp_archive = temp_dir_path / f"archive{self._get_extension_for_format(format_info)}"
            create_success, create_errors = self._create_archive_local(staged_paths, Path(temp_archive), format_info, completion_callback)
            success_count += create_success
            error_count += create_errors
            
            if create_success == 0:
                return (success_count, error_count)
            
            # Upload/move archive to final destination
            try:
                if archive_path.is_remote():
                    # Upload to remote storage
                    archive_path.write_bytes(temp_archive.read_bytes())
                    self.logger.info(f"Uploaded archive to: {archive_path}")
                else:
                    # Move to local destination
                    import shutil
                    shutil.move(str(temp_archive), str(archive_path))
                    self.logger.info(f"Moved archive to: {archive_path}")
            except PermissionError as e:
                self.logger.error(f"Permission denied moving archive to destination {archive_path.name}: {e}")
                error_count += 1
                self.progress_manager.increment_errors()
            except OSError as e:
                # Check for disk space exhaustion
                if "No space left" in str(e) or "Disk quota exceeded" in str(e):
                    self.logger.error(f"Disk space exhausted moving archive to destination: {e}")
                else:
                    self.logger.error(f"OS error moving archive to destination {archive_path.name}: {e}")
                error_count += 1
                self.progress_manager.increment_errors()
            except ArchiveError as e:
                self.logger.error(f"Archive error moving archive to destination: {e.user_message if hasattr(e, 'user_message') and e.user_message else str(e)}")
                error_count += 1
                self.progress_manager.increment_errors()
            except Exception as e:
                self.logger.error(f"Unexpected error moving archive to destination: {e}")
                error_count += 1
                self.progress_manager.increment_errors()
            
        except PermissionError as e:
            self.logger.error(f"Permission denied creating cross-storage archive: {e}")
            error_count += 1
            self.progress_manager.increment_errors()
        except OSError as e:
            # Check for disk space exhaustion
            if "No space left" in str(e) or "Disk quota exceeded" in str(e):
                self.logger.error(f"Disk space exhausted creating cross-storage archive: {e}")
            else:
                self.logger.error(f"OS error creating cross-storage archive: {e}")
            error_count += 1
            self.progress_manager.increment_errors()
        except ArchiveError as e:
            self.logger.error(f"Archive error creating cross-storage archive: {e.user_message if hasattr(e, 'user_message') and e.user_message else str(e)}")
            error_count += 1
            self.progress_manager.increment_errors()
        except Exception as e:
            self.logger.error(f"Unexpected error creating cross-storage archive: {e}")
            error_count += 1
            self.progress_manager.increment_errors()
        
        finally:
            # Clean up temporary directory
            if temp_dir and PathlibPath(temp_dir).exists():
                import shutil
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    self.logger.warning(f"Warning: Could not clean up temp directory: {e}")
        
        return (success_count, error_count)
    
    def _download_directory_recursive(self, remote_dir: Path, local_dir: Path):
        """
        Recursively download a remote directory to local storage.
        
        Migrated from ArchiveOperations._download_directory_recursive().
        
        Args:
            remote_dir: Remote directory path
            local_dir: Local directory path
        """
        try:
            for item in remote_dir.iterdir():
                # Check for cancellation
                if hasattr(self.file_manager, 'operation_cancelled') and self.file_manager.operation_cancelled:
                    break
                
                local_item = local_dir / item.name
                try:
                    if item.is_file():
                        local_item.write_bytes(item.read_bytes())
                    elif item.is_dir():
                        local_item.mkdir()
                        self._download_directory_recursive(item, local_item)
                except PermissionError as e:
                    self.logger.error(f"Permission denied downloading {item.name}: {e}")
                    # Continue with next item
                except OSError as e:
                    # Check for disk space exhaustion
                    if "No space left" in str(e) or "Disk quota exceeded" in str(e):
                        self.logger.error(f"Disk space exhausted downloading {item.name}: {e}")
                        # Stop operation - cannot continue
                        raise
                    else:
                        self.logger.error(f"OS error downloading {item.name}: {e}")
                        # Continue with next item
                except ArchiveError as e:
                    self.logger.error(f"Archive error downloading {item.name}: {e.user_message if hasattr(e, 'user_message') and e.user_message else str(e)}")
                    # Continue with next item
                except Exception as e:
                    self.logger.error(f"Unexpected error downloading {item.name}: {e}")
                    # Continue with next item
        except PermissionError as e:
            self.logger.error(f"Permission denied downloading directory {remote_dir.name}: {e}")
            raise
        except OSError as e:
            self.logger.error(f"OS error downloading directory {remote_dir.name}: {e}")
            raise
        except ArchiveError as e:
            self.logger.error(f"Archive error downloading directory {remote_dir.name}: {e.user_message if hasattr(e, 'user_message') and e.user_message else str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error downloading directory {remote_dir.name}: {e}")
            raise

    def _extract_archive_local(self, archive_path: Path, destination_dir: Path,
                              format_info: Dict, overwrite: bool, skip_files: List[str] = None,
                              completion_callback: Optional[Callable] = None) -> tuple:
        """
        Extract archive when both paths are local.
        
        Migrated from ArchiveOperations._extract_archive_local().
        
        Args:
            archive_path: Path to archive file
            destination_dir: Destination directory
            format_info: Archive format information
            overwrite: Whether to overwrite existing files
            skip_files: List of filenames to skip during extraction
            
        Returns:
            Tuple of (success_count, error_count, skipped_count)
        """
        success_count = 0
        error_count = 0
        skipped_count = 0
        skip_files = skip_files or []
        
        try:
            # Ensure destination directory exists
            destination_dir.mkdir(parents=True, exist_ok=True)
            
            if format_info['type'] == 'tar':
                mode = self._get_tar_mode(format_info, 'r')
                
                with tarfile.open(str(archive_path), mode) as tar:
                    members = tar.getmembers()
                    
                    for member in members:
                        # Check for cancellation
                        if hasattr(self.file_manager, 'operation_cancelled') and self.file_manager.operation_cancelled:
                            self.logger.info("Archive extraction cancelled")
                            break
                        
                        # Skip directories
                        if member.isdir():
                            continue
                        
                        # Check if file should be skipped
                        if member.name in skip_files:
                            self.logger.info(f"Skipping file (user choice): {member.name}")
                            skipped_count += 1
                            continue
                        
                        dest_path = destination_dir / member.name
                        
                        # Check for overwrite
                        if dest_path.exists() and not overwrite:
                            self.logger.warning(f"File exists, skipping: {member.name}")
                            skipped_count += 1
                            continue
                        
                        try:
                            # Extract the member
                            tar.extract(member, str(destination_dir))
                            success_count += 1
                            self.progress_manager.update_progress(member.name, success_count)
                            self.logger.info(f"Extracted: {member.name}")
                        except PermissionError as e:
                            self.logger.error(f"Permission denied extracting {member.name}: {e}")
                            error_count += 1
                            self.progress_manager.increment_errors()
                            # Continue with next file
                        except OSError as e:
                            # Check for disk space exhaustion
                            if "No space left" in str(e) or "Disk quota exceeded" in str(e):
                                self.logger.error(f"Disk space exhausted during extraction: {e}")
                                error_count += 1
                                self.progress_manager.increment_errors()
                                # Stop operation - cannot continue
                                break
                            else:
                                self.logger.error(f"OS error extracting {member.name}: {e}")
                                error_count += 1
                                self.progress_manager.increment_errors()
                                # Continue with next file
                        except ArchiveError as e:
                            self.logger.error(f"Archive error extracting {member.name}: {e.user_message if hasattr(e, 'user_message') and e.user_message else str(e)}")
                            error_count += 1
                            self.progress_manager.increment_errors()
                            # Continue with next file
                        except Exception as e:
                            self.logger.error(f"Unexpected error extracting {member.name}: {e}")
                            error_count += 1
                            self.progress_manager.increment_errors()
                            # Continue with next file
                    
                    self.logger.info(f"Extracted {success_count} items, skipped {skipped_count}")
            
            elif format_info['type'] == 'zip':
                with zipfile.ZipFile(str(archive_path), 'r') as zip_file:
                    members = zip_file.namelist()
                    
                    for member in members:
                        # Check for cancellation
                        if hasattr(self.file_manager, 'operation_cancelled') and self.file_manager.operation_cancelled:
                            self.logger.info("Archive extraction cancelled")
                            break
                        
                        # Skip directories
                        if member.endswith('/'):
                            continue
                        
                        # Check if file should be skipped
                        if member in skip_files:
                            self.logger.info(f"Skipping file (user choice): {member}")
                            skipped_count += 1
                            continue
                        
                        dest_path = destination_dir / member
                        
                        # Check for overwrite
                        if dest_path.exists() and not overwrite:
                            self.logger.warning(f"File exists, skipping: {member}")
                            skipped_count += 1
                            continue
                        
                        try:
                            # Extract the member
                            zip_file.extract(member, str(destination_dir))
                            success_count += 1
                            self.progress_manager.update_progress(member, success_count)
                            self.logger.info(f"Extracted: {member}")
                        except PermissionError as e:
                            self.logger.error(f"Permission denied extracting {member}: {e}")
                            error_count += 1
                            self.progress_manager.increment_errors()
                            # Continue with next file
                        except OSError as e:
                            # Check for disk space exhaustion
                            if "No space left" in str(e) or "Disk quota exceeded" in str(e):
                                self.logger.error(f"Disk space exhausted during extraction: {e}")
                                error_count += 1
                                self.progress_manager.increment_errors()
                                # Stop operation - cannot continue
                                break
                            else:
                                self.logger.error(f"OS error extracting {member}: {e}")
                                error_count += 1
                                self.progress_manager.increment_errors()
                                # Continue with next file
                        except ArchiveError as e:
                            self.logger.error(f"Archive error extracting {member}: {e.user_message if hasattr(e, 'user_message') and e.user_message else str(e)}")
                            error_count += 1
                            self.progress_manager.increment_errors()
                            # Continue with next file
                        except Exception as e:
                            self.logger.error(f"Unexpected error extracting {member}: {e}")
                            error_count += 1
                            self.progress_manager.increment_errors()
                            # Continue with next file
                    
                    self.logger.info(f"Extracted {success_count} items, skipped {skipped_count}")
            
            else:
                self.logger.error(f"Unsupported archive type for local extraction: {format_info['type']}")
                error_count += 1
                self.progress_manager.increment_errors()
                return (success_count, error_count, skipped_count)
            
            # Only log summary if no callback provided (callback suppresses default logging)
            if success_count > 0 and not completion_callback:
                self.logger.info(f"Archive extracted successfully to: {destination_dir}")
            
        except PermissionError as e:
            self.logger.error(f"Permission denied extracting archive {archive_path.name}: {e}")
            error_count += 1
            self.progress_manager.increment_errors()
        except OSError as e:
            # Check for disk space exhaustion
            if "No space left" in str(e) or "Disk quota exceeded" in str(e):
                self.logger.error(f"Disk space exhausted extracting archive {archive_path.name}: {e}")
            else:
                self.logger.error(f"OS error extracting archive {archive_path.name}: {e}")
            error_count += 1
            self.progress_manager.increment_errors()
        except ArchiveError as e:
            self.logger.error(f"Archive error extracting {archive_path.name}: {e.user_message if hasattr(e, 'user_message') and e.user_message else str(e)}")
            error_count += 1
            self.progress_manager.increment_errors()
        except Exception as e:
            self.logger.error(f"Unexpected error extracting local archive {archive_path.name}: {e}")
            error_count += 1
            self.progress_manager.increment_errors()
        
        return (success_count, error_count, skipped_count)

    def _extract_archive_cross_storage(self, archive_path: Path, destination_dir: Path,
                                      format_info: Dict, overwrite: bool, skip_files: List[str] = None) -> tuple:
        """
        Extract archive with cross-storage support using temporary files.
        
        Migrated from ArchiveOperations._extract_archive_cross_storage().
        
        Args:
            archive_path: Path to archive file
            destination_dir: Destination directory
            format_info: Archive format information
            overwrite: Whether to overwrite existing files
            skip_files: List of filenames to skip during extraction
            
        Returns:
            Tuple of (success_count, error_count, skipped_count)
        """
        temp_dir = None
        success_count = 0
        error_count = 0
        skipped_count = 0
        skip_files = skip_files or []
        
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix='tfm_extract_')
            temp_dir_path = PathlibPath(temp_dir)
            
            # Download archive to temporary location if remote
            if archive_path.is_remote():
                try:
                    temp_archive = temp_dir_path / archive_path.name
                    temp_archive.write_bytes(archive_path.read_bytes())
                    archive_to_extract = Path(temp_archive)
                    self.logger.info(f"Downloaded archive to temp: {archive_path.name}")
                except PermissionError as e:
                    self.logger.error(f"Permission denied downloading archive {archive_path.name}: {e}")
                    error_count += 1
                    self.progress_manager.increment_errors()
                    return (success_count, error_count, skipped_count)
                except OSError as e:
                    # Check for disk space exhaustion
                    if "No space left" in str(e) or "Disk quota exceeded" in str(e):
                        self.logger.error(f"Disk space exhausted downloading archive: {e}")
                    else:
                        self.logger.error(f"OS error downloading archive {archive_path.name}: {e}")
                    error_count += 1
                    self.progress_manager.increment_errors()
                    return (success_count, error_count, skipped_count)
                except ArchiveError as e:
                    self.logger.error(f"Archive error downloading archive: {e.user_message if hasattr(e, 'user_message') and e.user_message else str(e)}")
                    error_count += 1
                    self.progress_manager.increment_errors()
                    return (success_count, error_count, skipped_count)
                except Exception as e:
                    self.logger.error(f"Unexpected error downloading archive: {e}")
                    error_count += 1
                    self.progress_manager.increment_errors()
                    return (success_count, error_count, skipped_count)
            else:
                archive_to_extract = archive_path
            
            # Extract to temporary directory
            temp_extract_dir = temp_dir_path / 'extracted'
            temp_extract_dir.mkdir()
            
            extract_success, extract_errors, extract_skipped = self._extract_archive_local(
                archive_to_extract, Path(temp_extract_dir), format_info, overwrite=True, skip_files=skip_files, completion_callback=None
            )
            success_count += extract_success
            error_count += extract_errors
            skipped_count += extract_skipped
            
            if extract_success == 0:
                return (success_count, error_count, skipped_count)
            
            # Upload/move extracted files to final destination
            try:
                if destination_dir.is_remote():
                    # Upload extracted files to remote storage
                    self._upload_directory_recursive(Path(temp_extract_dir), destination_dir, overwrite)
                    self.logger.info(f"Uploaded extracted files to: {destination_dir}")
                else:
                    # Move extracted files to local destination
                    destination_dir.mkdir(parents=True, exist_ok=True)
                    for item in temp_extract_dir.iterdir():
                        # Check for cancellation
                        if hasattr(self.file_manager, 'operation_cancelled') and self.file_manager.operation_cancelled:
                            break
                        
                        dest_item = destination_dir / item.name
                        try:
                            if item.is_file():
                                if dest_item.exists() and not overwrite:
                                    self.logger.warning(f"File exists, skipping: {item.name}")
                                    continue
                                import shutil
                                shutil.copy2(str(item), str(dest_item))
                            elif item.is_dir():
                                if dest_item.exists() and not overwrite:
                                    self.logger.warning(f"Directory exists, skipping: {item.name}")
                                    continue
                                import shutil
                                shutil.copytree(str(item), str(dest_item))
                        except PermissionError as e:
                            self.logger.error(f"Permission denied moving {item.name}: {e}")
                            error_count += 1
                            self.progress_manager.increment_errors()
                            # Continue with next item
                        except OSError as e:
                            # Check for disk space exhaustion
                            if "No space left" in str(e) or "Disk quota exceeded" in str(e):
                                self.logger.error(f"Disk space exhausted moving extracted files: {e}")
                                error_count += 1
                                self.progress_manager.increment_errors()
                                # Stop operation - cannot continue
                                break
                            else:
                                self.logger.error(f"OS error moving {item.name}: {e}")
                                error_count += 1
                                self.progress_manager.increment_errors()
                                # Continue with next item
                        except ArchiveError as e:
                            self.logger.error(f"Archive error moving {item.name}: {e.user_message if hasattr(e, 'user_message') and e.user_message else str(e)}")
                            error_count += 1
                            self.progress_manager.increment_errors()
                            # Continue with next item
                        except Exception as e:
                            self.logger.error(f"Unexpected error moving {item.name}: {e}")
                            error_count += 1
                            self.progress_manager.increment_errors()
                            # Continue with next item
                    
                    self.logger.info(f"Moved extracted files to: {destination_dir}")
            except PermissionError as e:
                self.logger.error(f"Permission denied moving extracted files: {e}")
                error_count += 1
                self.progress_manager.increment_errors()
            except OSError as e:
                # Check for disk space exhaustion
                if "No space left" in str(e) or "Disk quota exceeded" in str(e):
                    self.logger.error(f"Disk space exhausted moving extracted files: {e}")
                else:
                    self.logger.error(f"OS error moving extracted files: {e}")
                error_count += 1
                self.progress_manager.increment_errors()
            except ArchiveError as e:
                self.logger.error(f"Archive error moving extracted files: {e.user_message if hasattr(e, 'user_message') and e.user_message else str(e)}")
                error_count += 1
                self.progress_manager.increment_errors()
            except Exception as e:
                self.logger.error(f"Unexpected error moving extracted files: {e}")
                error_count += 1
                self.progress_manager.increment_errors()
            
        except PermissionError as e:
            self.logger.error(f"Permission denied extracting cross-storage archive: {e}")
            error_count += 1
            self.progress_manager.increment_errors()
        except OSError as e:
            # Check for disk space exhaustion
            if "No space left" in str(e) or "Disk quota exceeded" in str(e):
                self.logger.error(f"Disk space exhausted extracting cross-storage archive: {e}")
            else:
                self.logger.error(f"OS error extracting cross-storage archive: {e}")
            error_count += 1
            self.progress_manager.increment_errors()
        except ArchiveError as e:
            self.logger.error(f"Archive error extracting cross-storage archive: {e.user_message if hasattr(e, 'user_message') and e.user_message else str(e)}")
            error_count += 1
            self.progress_manager.increment_errors()
        except Exception as e:
            self.logger.error(f"Unexpected error extracting cross-storage archive: {e}")
            error_count += 1
            self.progress_manager.increment_errors()
        
        finally:
            # Clean up temporary directory
            if temp_dir and PathlibPath(temp_dir).exists():
                import shutil
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    self.logger.warning(f"Warning: Could not clean up temp directory: {e}")
        
        return (success_count, error_count, skipped_count)
    
    def _upload_directory_recursive(self, local_dir: Path, remote_dir: Path, overwrite: bool):
        """
        Recursively upload a local directory to remote storage.
        
        Migrated from ArchiveOperations._upload_directory_recursive().
        
        Args:
            local_dir: Local directory path
            remote_dir: Remote directory path
            overwrite: Whether to overwrite existing files
        """
        try:
            # Ensure remote directory exists
            if not remote_dir.exists():
                remote_dir.mkdir(parents=True, exist_ok=True)
            
            for item in local_dir.iterdir():
                # Check for cancellation
                if hasattr(self.file_manager, 'operation_cancelled') and self.file_manager.operation_cancelled:
                    break
                
                remote_item = remote_dir / item.name
                try:
                    if item.is_file():
                        if remote_item.exists() and not overwrite:
                            self.logger.warning(f"Remote file exists, skipping: {item.name}")
                            continue
                        remote_item.write_bytes(item.read_bytes())
                    elif item.is_dir():
                        if not remote_item.exists():
                            remote_item.mkdir(parents=True, exist_ok=True)
                        self._upload_directory_recursive(item, remote_item, overwrite)
                except PermissionError as e:
                    self.logger.error(f"Permission denied uploading {item.name}: {e}")
                    # Continue with next item
                except OSError as e:
                    # Check for disk space exhaustion
                    if "No space left" in str(e) or "Disk quota exceeded" in str(e):
                        self.logger.error(f"Disk space exhausted uploading {item.name}: {e}")
                        # Stop operation - cannot continue
                        raise
                    else:
                        self.logger.error(f"OS error uploading {item.name}: {e}")
                        # Continue with next item
                except ArchiveError as e:
                    self.logger.error(f"Archive error uploading {item.name}: {e.user_message if hasattr(e, 'user_message') and e.user_message else str(e)}")
                    # Continue with next item
                except Exception as e:
                    self.logger.error(f"Unexpected error uploading {item.name}: {e}")
                    # Continue with next item
        except PermissionError as e:
            self.logger.error(f"Permission denied uploading directory {local_dir.name}: {e}")
            raise
        except OSError as e:
            self.logger.error(f"OS error uploading directory {local_dir.name}: {e}")
            raise
        except ArchiveError as e:
            self.logger.error(f"Archive error uploading directory {local_dir.name}: {e.user_message if hasattr(e, 'user_message') and e.user_message else str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error uploading directory {local_dir.name}: {e}")
            raise
