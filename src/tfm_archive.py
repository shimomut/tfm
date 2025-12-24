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
import stat
import io
import time
import threading
import fnmatch
from dataclasses import dataclass
from pathlib import Path as PathlibPath
from tfm_path import Path, PathImpl
from tfm_progress_manager import ProgressManager, OperationType
from typing import List, Optional, Union, Tuple, Dict, Any, Iterator


@dataclass
class ArchiveEntry:
    """
    Represents an entry (file or directory) within an archive.
    
    This dataclass provides a unified representation of archive entries
    across different archive formats (zip, tar, etc.).
    """
    name: str                    # Entry name (filename or dirname)
    internal_path: str           # Full path within archive
    is_dir: bool                 # Whether this is a directory
    size: int                    # Uncompressed size in bytes
    compressed_size: int         # Compressed size in bytes
    mtime: float                 # Modification time as timestamp
    mode: int                    # File permissions (Unix-style)
    archive_type: str            # Archive format ('zip', 'tar', 'tar.gz', etc.)
    
    def to_stat_result(self):
        """
        Convert ArchiveEntry to a stat_result-like object.
        
        This allows archive entries to be used with code that expects
        os.stat_result objects.
        
        Returns:
            os.stat_result: A stat_result object representing this entry
        """
        # Create a stat_result with the entry's metadata
        # Use os.stat_result constructor with a sequence of 10 values:
        # (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime)
        
        # Determine the file type bits for mode
        if self.is_dir:
            # Directory mode
            file_mode = stat.S_IFDIR | self.mode
        else:
            # Regular file mode
            file_mode = stat.S_IFREG | self.mode
        
        # Create stat_result with appropriate values
        # We use dummy values for fields that don't apply to archive entries
        stat_values = (
            file_mode,      # st_mode: file type and permissions
            0,              # st_ino: inode number (not applicable)
            0,              # st_dev: device (not applicable)
            1,              # st_nlink: number of hard links
            0,              # st_uid: user ID (not applicable)
            0,              # st_gid: group ID (not applicable)
            self.size,      # st_size: size in bytes
            self.mtime,     # st_atime: access time
            self.mtime,     # st_mtime: modification time
            self.mtime      # st_ctime: creation time
        )
        
        return os.stat_result(stat_values)
    
    @classmethod
    def from_zip_info(cls, zip_info: zipfile.ZipInfo, archive_type: str = 'zip') -> 'ArchiveEntry':
        """
        Create an ArchiveEntry from a ZipInfo object.
        
        Args:
            zip_info: ZipInfo object from zipfile module
            archive_type: Type of archive (default: 'zip')
            
        Returns:
            ArchiveEntry: New entry created from zip info
        """
        # Extract name and determine if it's a directory
        internal_path = zip_info.filename
        is_dir = zip_info.is_dir()
        
        # Get the entry name (last component of path)
        name = internal_path.rstrip('/').split('/')[-1] if internal_path else ''
        
        # Get sizes
        size = zip_info.file_size
        compressed_size = zip_info.compress_size
        
        # Convert date_time tuple to timestamp
        # ZipInfo.date_time is a tuple: (year, month, day, hour, minute, second)
        import time
        import datetime
        if zip_info.date_time:
            dt = datetime.datetime(*zip_info.date_time)
            mtime = dt.timestamp()
        else:
            mtime = 0.0
        
        # Extract Unix permissions from external_attr
        # For Unix systems, permissions are in the high 16 bits
        # Default to 0o644 for files, 0o755 for directories
        if zip_info.external_attr:
            mode = (zip_info.external_attr >> 16) & 0o777
        else:
            mode = 0o755 if is_dir else 0o644
        
        return cls(
            name=name,
            internal_path=internal_path,
            is_dir=is_dir,
            size=size,
            compressed_size=compressed_size,
            mtime=mtime,
            mode=mode,
            archive_type=archive_type
        )
    
    @classmethod
    def from_tar_info(cls, tar_info: tarfile.TarInfo, archive_type: str = 'tar') -> 'ArchiveEntry':
        """
        Create an ArchiveEntry from a TarInfo object.
        
        Args:
            tar_info: TarInfo object from tarfile module
            archive_type: Type of archive (e.g., 'tar', 'tar.gz', 'tar.bz2')
            
        Returns:
            ArchiveEntry: New entry created from tar info
        """
        # Extract name and path
        internal_path = tar_info.name
        is_dir = tar_info.isdir()
        
        # Get the entry name (last component of path)
        name = internal_path.rstrip('/').split('/')[-1] if internal_path else ''
        
        # Get sizes
        size = tar_info.size
        # For tar files, compressed size is not directly available
        # We'll use the same as uncompressed size as an approximation
        compressed_size = tar_info.size
        
        # Get modification time
        mtime = float(tar_info.mtime) if tar_info.mtime else 0.0
        
        # Get Unix permissions
        mode = tar_info.mode if tar_info.mode else (0o755 if is_dir else 0o644)
        
        return cls(
            name=name,
            internal_path=internal_path,
            is_dir=is_dir,
            size=size,
            compressed_size=compressed_size,
            mtime=mtime,
            mode=mode,
            archive_type=archive_type
        )


class ArchiveError(Exception):
    """Base exception for archive operations"""
    def __init__(self, message: str, user_message: Optional[str] = None):
        """
        Initialize archive error with technical and user-friendly messages.
        
        Args:
            message: Technical error message for logging
            user_message: User-friendly error message (defaults to message if not provided)
        """
        super().__init__(message)
        self.user_message = user_message or message


class ArchiveFormatError(ArchiveError):
    """Unsupported or invalid archive format"""
    pass


class ArchiveCorruptedError(ArchiveError):
    """Archive file is corrupted"""
    pass


class ArchiveExtractionError(ArchiveError):
    """Error during file extraction"""
    pass


class ArchiveNavigationError(ArchiveError):
    """Error navigating within archive"""
    pass


class ArchivePermissionError(ArchiveError):
    """Permission denied for archive operation"""
    pass


class ArchiveDiskSpaceError(ArchiveError):
    """Insufficient disk space for archive operation"""
    pass


class ArchiveHandler:
    """
    Base class for handling archive file access and caching of archive contents.
    
    This class provides a unified interface for reading archive files and
    extracting their contents, with support for different archive formats
    through format-specific subclasses.
    """
    
    def __init__(self, archive_path: Path):
        """
        Initialize handler for specific archive file.
        
        Args:
            archive_path: Path to the archive file
        """
        self._archive_path = archive_path
        self._archive_obj = None
        self._entry_cache: Dict[str, ArchiveEntry] = {}
        self._directory_cache: Dict[str, List[str]] = {}
        self._is_open = False
        self._last_access = 0.0
    
    def open(self):
        """
        Open the archive file and cache its structure.
        
        Raises:
            ArchiveCorruptedError: If archive is corrupted
            ArchiveFormatError: If archive format is invalid
            FileNotFoundError: If archive file doesn't exist
        """
        raise NotImplementedError("Subclasses must implement open()")
    
    def close(self):
        """Close the archive file"""
        if self._archive_obj:
            try:
                self._archive_obj.close()
            except Exception:
                pass
            self._archive_obj = None
        self._is_open = False
    
    def list_entries(self, internal_path: str = "") -> List[ArchiveEntry]:
        """
        List entries at the given internal path.
        
        Args:
            internal_path: Path within archive (empty string for root)
            
        Returns:
            List of ArchiveEntry objects for direct children
            
        Raises:
            ArchiveNavigationError: If path doesn't exist in archive
        """
        raise NotImplementedError("Subclasses must implement list_entries()")
    
    def get_entry_info(self, internal_path: str) -> Optional[ArchiveEntry]:
        """
        Get information about a specific entry.
        
        Args:
            internal_path: Path to entry within archive
            
        Returns:
            ArchiveEntry object or None if not found
        """
        raise NotImplementedError("Subclasses must implement get_entry_info()")
    
    def extract_to_bytes(self, internal_path: str) -> bytes:
        """
        Extract a file's contents to memory.
        
        Args:
            internal_path: Path to file within archive
            
        Returns:
            File contents as bytes
            
        Raises:
            ArchiveExtractionError: If extraction fails
            FileNotFoundError: If file doesn't exist in archive
        """
        raise NotImplementedError("Subclasses must implement extract_to_bytes()")
    
    def extract_to_file(self, internal_path: str, target_path: Path):
        """
        Extract a file to the filesystem.
        
        Args:
            internal_path: Path to file within archive
            target_path: Destination path on filesystem
            
        Raises:
            ArchiveExtractionError: If extraction fails
            FileNotFoundError: If file doesn't exist in archive
        """
        raise NotImplementedError("Subclasses must implement extract_to_file()")
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize internal archive path.
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized path (no leading slash, consistent separators)
        """
        # Remove leading/trailing slashes
        path = path.strip('/')
        # Normalize path separators
        path = path.replace('\\', '/')
        return path
    
    def __enter__(self):
        """Context manager entry"""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        return False


class ZipHandler(ArchiveHandler):
    """Handler for ZIP archive files"""
    
    def open(self):
        """Open the ZIP archive and cache its structure"""
        try:
            if not self._archive_path.exists():
                raise FileNotFoundError(
                    f"Archive not found: {self._archive_path}",
                    f"Archive file '{self._archive_path.name}' does not exist"
                )
            
            # For remote files, download to temp location
            if self._archive_path.is_remote():
                try:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
                    temp_file.write(self._archive_path.read_bytes())
                    temp_file.close()
                    archive_to_open = temp_file.name
                    self._temp_file = temp_file.name
                except PermissionError as e:
                    raise ArchivePermissionError(
                        f"Permission denied downloading archive: {e}",
                        f"Cannot download archive '{self._archive_path.name}': Permission denied"
                    )
                except OSError as e:
                    if "No space left on device" in str(e) or "Disk quota exceeded" in str(e):
                        raise ArchiveDiskSpaceError(
                            f"Insufficient disk space: {e}",
                            "Insufficient disk space to download archive"
                        )
                    raise ArchiveError(
                        f"Error downloading archive: {e}",
                        f"Cannot download archive '{self._archive_path.name}': {e}"
                    )
            else:
                archive_to_open = str(self._archive_path)
                self._temp_file = None
            
            # Open the ZIP file
            try:
                self._archive_obj = zipfile.ZipFile(archive_to_open, 'r')
            except PermissionError as e:
                raise ArchivePermissionError(
                    f"Permission denied opening archive: {e}",
                    f"Cannot open archive '{self._archive_path.name}': Permission denied"
                )
            
            self._is_open = True
            
            # Cache all entries
            self._cache_entries()
            
        except FileNotFoundError:
            # Re-raise FileNotFoundError with user-friendly message
            raise FileNotFoundError(
                f"Archive not found: {self._archive_path}",
                f"Archive file '{self._archive_path.name}' does not exist"
            )
        except zipfile.BadZipFile as e:
            raise ArchiveCorruptedError(
                f"Corrupted ZIP archive: {e}",
                f"Archive '{self._archive_path.name}' is corrupted or invalid"
            )
        except (ArchivePermissionError, ArchiveDiskSpaceError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            raise ArchiveFormatError(
                f"Error opening ZIP archive: {e}",
                f"Cannot open archive '{self._archive_path.name}': {e}"
            )
    
    def close(self):
        """Close the ZIP archive and clean up temp files"""
        super().close()
        if hasattr(self, '_temp_file') and self._temp_file:
            try:
                os.unlink(self._temp_file)
            except Exception:
                pass
            self._temp_file = None
    
    def _cache_entries(self):
        """Cache all entries from the ZIP file with lazy loading optimization"""
        if not self._archive_obj:
            return
        
        # Clear caches
        self._entry_cache.clear()
        self._directory_cache.clear()
        
        # Track all directories we've seen (including virtual ones)
        all_directories = set()
        
        # For large archives, use lazy loading - only cache structure, not all entries
        infolist = self._archive_obj.infolist()
        is_large_archive = len(infolist) > 1000
        
        # Process all entries
        for zip_info in infolist:
            entry = ArchiveEntry.from_zip_info(zip_info, 'zip')
            normalized_path = self._normalize_path(entry.internal_path)
            
            # For large archives, only cache directory structure initially
            # Individual entries will be loaded on demand
            if not is_large_archive or entry.is_dir or normalized_path.count('/') < 2:
                # Cache the entry (all entries for small archives, only shallow for large)
                self._entry_cache[normalized_path] = entry
            
            # Build directory cache and track parent directories
            if normalized_path:
                # Get all parent directories
                parts = normalized_path.split('/')
                for i in range(len(parts)):
                    if i == 0:
                        parent = ''
                    else:
                        parent = '/'.join(parts[:i])
                    
                    # Track this directory
                    if i < len(parts) - 1 or entry.is_dir:
                        dir_path = '/'.join(parts[:i+1]) if i < len(parts) - 1 else normalized_path
                        if dir_path:
                            all_directories.add(dir_path)
                    
                    # Add to parent's children list
                    if i < len(parts):
                        child = '/'.join(parts[:i+1])
                        if parent not in self._directory_cache:
                            self._directory_cache[parent] = []
                        if child not in self._directory_cache[parent]:
                            self._directory_cache[parent].append(child)
        
        # Create virtual directory entries for directories that don't have explicit entries
        for dir_path in all_directories:
            if dir_path and dir_path not in self._entry_cache:
                # Create a virtual directory entry
                virtual_entry = ArchiveEntry(
                    name=dir_path.split('/')[-1],
                    internal_path=dir_path,
                    is_dir=True,
                    size=0,
                    compressed_size=0,
                    mtime=0.0,
                    mode=0o755,
                    archive_type='zip'
                )
                self._entry_cache[dir_path] = virtual_entry
    
    def list_entries(self, internal_path: str = "") -> List[ArchiveEntry]:
        """List entries at the given internal path"""
        if not self._is_open:
            self.open()
        
        normalized_path = self._normalize_path(internal_path)
        
        # Get direct children from directory cache
        if normalized_path not in self._directory_cache:
            # Path doesn't exist or has no children
            if normalized_path and normalized_path not in self._entry_cache:
                raise ArchiveNavigationError(f"Path not found in archive: {internal_path}")
            return []
        
        # Return entries for direct children only
        entries = []
        for child_path in self._directory_cache[normalized_path]:
            if child_path in self._entry_cache:
                entries.append(self._entry_cache[child_path])
        
        return entries
    
    def get_entry_info(self, internal_path: str) -> Optional[ArchiveEntry]:
        """Get information about a specific entry with lazy loading"""
        if not self._is_open:
            self.open()
        
        normalized_path = self._normalize_path(internal_path)
        
        # Check cache first
        if normalized_path in self._entry_cache:
            return self._entry_cache[normalized_path]
        
        # For large archives with lazy loading, load entry on demand
        if self._archive_obj:
            try:
                zip_info = self._archive_obj.getinfo(normalized_path)
                entry = ArchiveEntry.from_zip_info(zip_info, 'zip')
                self._entry_cache[normalized_path] = entry
                return entry
            except KeyError:
                # Entry doesn't exist
                return None
        
        return None
    
    def extract_to_bytes(self, internal_path: str) -> bytes:
        """Extract a file's contents to memory"""
        if not self._is_open:
            self.open()
        
        normalized_path = self._normalize_path(internal_path)
        
        # Check if entry exists (with lazy loading)
        entry = self.get_entry_info(normalized_path)
        if not entry:
            raise FileNotFoundError(
                f"File not found in archive: {internal_path}",
                f"File '{internal_path}' does not exist in archive"
            )
        
        if entry.is_dir:
            raise ArchiveExtractionError(
                f"Cannot extract directory as bytes: {internal_path}",
                f"'{internal_path}' is a directory, not a file"
            )
        
        try:
            # Extract file contents
            return self._archive_obj.read(entry.internal_path)
        except PermissionError as e:
            raise ArchivePermissionError(
                f"Permission denied extracting file: {e}",
                f"Cannot extract '{internal_path}': Permission denied"
            )
        except OSError as e:
            if "No space left on device" in str(e) or "Disk quota exceeded" in str(e):
                raise ArchiveDiskSpaceError(
                    f"Insufficient disk space: {e}",
                    "Insufficient disk space to extract file"
                )
            raise ArchiveExtractionError(
                f"Error extracting file: {e}",
                f"Cannot extract '{internal_path}': {e}"
            )
        except Exception as e:
            raise ArchiveExtractionError(
                f"Error extracting file: {e}",
                f"Cannot extract '{internal_path}': {e}"
            )
    
    def extract_to_file(self, internal_path: str, target_path: Path):
        """Extract a file to the filesystem"""
        if not self._is_open:
            self.open()
        
        normalized_path = self._normalize_path(internal_path)
        
        # Check if entry exists
        entry = self._entry_cache.get(normalized_path)
        if not entry:
            raise FileNotFoundError(
                f"File not found in archive: {internal_path}",
                f"File '{internal_path}' does not exist in archive"
            )
        
        if entry.is_dir:
            raise ArchiveExtractionError(
                f"Cannot extract directory as file: {internal_path}",
                f"'{internal_path}' is a directory, not a file"
            )
        
        try:
            # Extract file contents
            data = self._archive_obj.read(entry.internal_path)
            
            # Write to target
            try:
                target_path.write_bytes(data)
            except PermissionError as e:
                raise ArchivePermissionError(
                    f"Permission denied writing to target: {e}",
                    f"Cannot write to '{target_path}': Permission denied"
                )
            except OSError as e:
                if "No space left on device" in str(e) or "Disk quota exceeded" in str(e):
                    raise ArchiveDiskSpaceError(
                        f"Insufficient disk space: {e}",
                        "Insufficient disk space to extract file"
                    )
                raise ArchiveExtractionError(
                    f"Error writing to target: {e}",
                    f"Cannot write to '{target_path}': {e}"
                )
            
            # Try to preserve modification time
            try:
                os.utime(str(target_path), (entry.mtime, entry.mtime))
            except Exception:
                pass  # Ignore errors setting mtime
            
        except (ArchivePermissionError, ArchiveDiskSpaceError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            raise ArchiveExtractionError(
                f"Error extracting file: {e}",
                f"Cannot extract '{internal_path}': {e}"
            )


class TarHandler(ArchiveHandler):
    """Handler for TAR archive files (including compressed variants)"""
    
    def __init__(self, archive_path: Path, compression: Optional[str] = None):
        """
        Initialize TAR handler.
        
        Args:
            archive_path: Path to the archive file
            compression: Compression type ('gz', 'bz2', 'xz', or None)
        """
        super().__init__(archive_path)
        self._compression = compression
    
    def open(self):
        """Open the TAR archive and cache its structure"""
        try:
            if not self._archive_path.exists():
                raise FileNotFoundError(
                    f"Archive not found: {self._archive_path}",
                    f"Archive file '{self._archive_path.name}' does not exist"
                )
            
            # Determine open mode
            if self._compression == 'gz':
                mode = 'r:gz'
            elif self._compression == 'bz2':
                mode = 'r:bz2'
            elif self._compression == 'xz':
                mode = 'r:xz'
            else:
                mode = 'r'
            
            # For remote files, download to temp location
            if self._archive_path.is_remote():
                try:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tar')
                    temp_file.write(self._archive_path.read_bytes())
                    temp_file.close()
                    archive_to_open = temp_file.name
                    self._temp_file = temp_file.name
                except PermissionError as e:
                    raise ArchivePermissionError(
                        f"Permission denied downloading archive: {e}",
                        f"Cannot download archive '{self._archive_path.name}': Permission denied"
                    )
                except OSError as e:
                    if "No space left on device" in str(e) or "Disk quota exceeded" in str(e):
                        raise ArchiveDiskSpaceError(
                            f"Insufficient disk space: {e}",
                            "Insufficient disk space to download archive"
                        )
                    raise ArchiveError(
                        f"Error downloading archive: {e}",
                        f"Cannot download archive '{self._archive_path.name}': {e}"
                    )
            else:
                archive_to_open = str(self._archive_path)
                self._temp_file = None
            
            # Open the TAR file
            try:
                self._archive_obj = tarfile.open(archive_to_open, mode)
            except PermissionError as e:
                raise ArchivePermissionError(
                    f"Permission denied opening archive: {e}",
                    f"Cannot open archive '{self._archive_path.name}': Permission denied"
                )
            
            self._is_open = True
            
            # Cache all entries
            self._cache_entries()
            
        except FileNotFoundError:
            # Re-raise FileNotFoundError with user-friendly message
            raise FileNotFoundError(
                f"Archive not found: {self._archive_path}",
                f"Archive file '{self._archive_path.name}' does not exist"
            )
        except tarfile.TarError as e:
            raise ArchiveCorruptedError(
                f"Corrupted TAR archive: {e}",
                f"Archive '{self._archive_path.name}' is corrupted or invalid"
            )
        except (ArchivePermissionError, ArchiveDiskSpaceError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            raise ArchiveFormatError(
                f"Error opening TAR archive: {e}",
                f"Cannot open archive '{self._archive_path.name}': {e}"
            )
    
    def close(self):
        """Close the TAR archive and clean up temp files"""
        super().close()
        if hasattr(self, '_temp_file') and self._temp_file:
            try:
                os.unlink(self._temp_file)
            except Exception:
                pass
            self._temp_file = None
    
    def _cache_entries(self):
        """Cache all entries from the TAR file"""
        if not self._archive_obj:
            return
        
        # Clear caches
        self._entry_cache.clear()
        self._directory_cache.clear()
        
        # Determine archive type string
        if self._compression == 'gz':
            archive_type = 'tar.gz'
        elif self._compression == 'bz2':
            archive_type = 'tar.bz2'
        elif self._compression == 'xz':
            archive_type = 'tar.xz'
        else:
            archive_type = 'tar'
        
        # Track all directories we've seen (including virtual ones)
        all_directories = set()
        
        # Process all entries
        for tar_info in self._archive_obj.getmembers():
            entry = ArchiveEntry.from_tar_info(tar_info, archive_type)
            normalized_path = self._normalize_path(entry.internal_path)
            
            # Cache the entry
            self._entry_cache[normalized_path] = entry
            
            # Build directory cache and track parent directories
            if normalized_path:
                # Get all parent directories
                parts = normalized_path.split('/')
                for i in range(len(parts)):
                    if i == 0:
                        parent = ''
                    else:
                        parent = '/'.join(parts[:i])
                    
                    # Track this directory
                    if i < len(parts) - 1 or entry.is_dir:
                        dir_path = '/'.join(parts[:i+1]) if i < len(parts) - 1 else normalized_path
                        if dir_path:
                            all_directories.add(dir_path)
                    
                    # Add to parent's children list
                    if i < len(parts):
                        child = '/'.join(parts[:i+1])
                        if parent not in self._directory_cache:
                            self._directory_cache[parent] = []
                        if child not in self._directory_cache[parent]:
                            self._directory_cache[parent].append(child)
        
        # Create virtual directory entries for directories that don't have explicit entries
        for dir_path in all_directories:
            if dir_path and dir_path not in self._entry_cache:
                # Create a virtual directory entry
                virtual_entry = ArchiveEntry(
                    name=dir_path.split('/')[-1],
                    internal_path=dir_path,
                    is_dir=True,
                    size=0,
                    compressed_size=0,
                    mtime=0.0,
                    mode=0o755,
                    archive_type=archive_type
                )
                self._entry_cache[dir_path] = virtual_entry
    
    def list_entries(self, internal_path: str = "") -> List[ArchiveEntry]:
        """List entries at the given internal path"""
        if not self._is_open:
            self.open()
        
        normalized_path = self._normalize_path(internal_path)
        
        # Get direct children from directory cache
        if normalized_path not in self._directory_cache:
            # Path doesn't exist or has no children
            if normalized_path and normalized_path not in self._entry_cache:
                raise ArchiveNavigationError(f"Path not found in archive: {internal_path}")
            return []
        
        # Return entries for direct children only
        entries = []
        for child_path in self._directory_cache[normalized_path]:
            if child_path in self._entry_cache:
                entries.append(self._entry_cache[child_path])
        
        return entries
    
    def get_entry_info(self, internal_path: str) -> Optional[ArchiveEntry]:
        """Get information about a specific entry"""
        if not self._is_open:
            self.open()
        
        normalized_path = self._normalize_path(internal_path)
        return self._entry_cache.get(normalized_path)
    
    def extract_to_bytes(self, internal_path: str) -> bytes:
        """Extract a file's contents to memory"""
        if not self._is_open:
            self.open()
        
        normalized_path = self._normalize_path(internal_path)
        
        # Check if entry exists
        entry = self._entry_cache.get(normalized_path)
        if not entry:
            raise FileNotFoundError(
                f"File not found in archive: {internal_path}",
                f"File '{internal_path}' does not exist in archive"
            )
        
        if entry.is_dir:
            raise ArchiveExtractionError(
                f"Cannot extract directory as bytes: {internal_path}",
                f"'{internal_path}' is a directory, not a file"
            )
        
        try:
            # Extract file contents
            file_obj = self._archive_obj.extractfile(entry.internal_path)
            if file_obj is None:
                raise ArchiveExtractionError(
                    f"Cannot extract file: {internal_path}",
                    f"Cannot extract '{internal_path}' from archive"
                )
            
            return file_obj.read()
        except ArchiveExtractionError:
            # Re-raise our custom exception
            raise
        except PermissionError as e:
            raise ArchivePermissionError(
                f"Permission denied extracting file: {e}",
                f"Cannot extract '{internal_path}': Permission denied"
            )
        except OSError as e:
            if "No space left on device" in str(e) or "Disk quota exceeded" in str(e):
                raise ArchiveDiskSpaceError(
                    f"Insufficient disk space: {e}",
                    "Insufficient disk space to extract file"
                )
            raise ArchiveExtractionError(
                f"Error extracting file: {e}",
                f"Cannot extract '{internal_path}': {e}"
            )
        except Exception as e:
            raise ArchiveExtractionError(
                f"Error extracting file: {e}",
                f"Cannot extract '{internal_path}': {e}"
            )
    
    def extract_to_file(self, internal_path: str, target_path: Path):
        """Extract a file to the filesystem"""
        if not self._is_open:
            self.open()
        
        normalized_path = self._normalize_path(internal_path)
        
        # Check if entry exists
        entry = self._entry_cache.get(normalized_path)
        if not entry:
            raise FileNotFoundError(
                f"File not found in archive: {internal_path}",
                f"File '{internal_path}' does not exist in archive"
            )
        
        if entry.is_dir:
            raise ArchiveExtractionError(
                f"Cannot extract directory as file: {internal_path}",
                f"'{internal_path}' is a directory, not a file"
            )
        
        try:
            # Extract file contents
            file_obj = self._archive_obj.extractfile(entry.internal_path)
            if file_obj is None:
                raise ArchiveExtractionError(
                    f"Cannot extract file: {internal_path}",
                    f"Cannot extract '{internal_path}' from archive"
                )
            
            data = file_obj.read()
            
            # Write to target
            try:
                target_path.write_bytes(data)
            except PermissionError as e:
                raise ArchivePermissionError(
                    f"Permission denied writing to target: {e}",
                    f"Cannot write to '{target_path}': Permission denied"
                )
            except OSError as e:
                if "No space left on device" in str(e) or "Disk quota exceeded" in str(e):
                    raise ArchiveDiskSpaceError(
                        f"Insufficient disk space: {e}",
                        "Insufficient disk space to extract file"
                    )
                raise ArchiveExtractionError(
                    f"Error writing to target: {e}",
                    f"Cannot write to '{target_path}': {e}"
                )
            
            # Try to preserve modification time and permissions
            try:
                os.utime(str(target_path), (entry.mtime, entry.mtime))
                os.chmod(str(target_path), entry.mode)
            except Exception:
                pass  # Ignore errors setting metadata
            
        except (ArchivePermissionError, ArchiveDiskSpaceError, ArchiveExtractionError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            raise ArchiveExtractionError(
                f"Error extracting file: {e}",
                f"Cannot extract '{internal_path}': {e}"
            )


class ArchiveCache:
    """
    Cache for opened archives and their structures.
    
    Features:
    - LRU eviction policy to limit memory usage
    - Configurable TTL (time-to-live) for cached structures
    - Thread-safe operations with locks
    - Lazy initialization of archive handlers
    - Cache statistics and monitoring
    - Performance metrics tracking
    """
    
    def __init__(self, max_open: int = 5, ttl: int = 300):
        """
        Initialize cache.
        
        Args:
            max_open: Maximum number of archives to keep open (default: 5)
            ttl: Time-to-live for cached structures in seconds (default: 300)
        """
        self._max_open = max_open
        self._ttl = ttl
        self._handlers: Dict[str, ArchiveHandler] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = threading.RLock()
        
        # Performance metrics
        self._cache_hits = 0
        self._cache_misses = 0
        self._evictions = 0
        self._total_open_time = 0.0
    
    def get_handler(self, archive_path: Path) -> ArchiveHandler:
        """
        Get or create handler for archive with lazy initialization.
        
        Args:
            archive_path: Path to the archive file
            
        Returns:
            ArchiveHandler: Handler for the archive
            
        Raises:
            ArchiveError: If archive cannot be opened
        """
        # Convert path to string for cache key
        cache_key = str(archive_path.absolute())
        current_time = time.time()
        
        with self._lock:
            # Check if handler exists and is still valid
            if cache_key in self._handlers:
                handler = self._handlers[cache_key]
                access_time = self._access_times.get(cache_key, 0)
                
                # Check if handler has expired
                if current_time - access_time > self._ttl:
                    # Handler expired, close and remove it
                    try:
                        handler.close()
                    except Exception:
                        pass
                    del self._handlers[cache_key]
                    del self._access_times[cache_key]
                    self._cache_misses += 1
                else:
                    # Handler is valid, update access time and return
                    self._access_times[cache_key] = current_time
                    self._cache_hits += 1
                    return handler
            else:
                self._cache_misses += 1
            
            # Need to create new handler
            # First, enforce max_open limit using LRU eviction
            if len(self._handlers) >= self._max_open:
                self._evict_lru()
            
            # Create appropriate handler based on archive format
            handler = self._create_handler(archive_path)
            
            # Open the handler (lazy initialization) and track time
            open_start = time.time()
            handler.open()
            open_duration = time.time() - open_start
            self._total_open_time += open_duration
            
            # Cache the handler
            self._handlers[cache_key] = handler
            self._access_times[cache_key] = current_time
            
            return handler
    
    def _create_handler(self, archive_path: Path) -> ArchiveHandler:
        """
        Create appropriate handler for archive format.
        
        Args:
            archive_path: Path to the archive file
            
        Returns:
            ArchiveHandler: Appropriate handler for the archive format
            
        Raises:
            ArchiveFormatError: If archive format is not supported
        """
        filename = archive_path.name.lower()
        
        # Check for ZIP format
        if filename.endswith('.zip'):
            return ZipHandler(archive_path)
        
        # Check for TAR formats
        if filename.endswith('.tar'):
            return TarHandler(archive_path, compression=None)
        elif filename.endswith('.tar.gz') or filename.endswith('.tgz'):
            return TarHandler(archive_path, compression='gz')
        elif filename.endswith('.tar.bz2') or filename.endswith('.tbz2'):
            return TarHandler(archive_path, compression='bz2')
        elif filename.endswith('.tar.xz') or filename.endswith('.txz'):
            return TarHandler(archive_path, compression='xz')
        
        # Unsupported format
        raise ArchiveFormatError(f"Unsupported archive format: {filename}")
    
    def invalidate(self, archive_path: Path):
        """
        Invalidate cache for specific archive.
        
        Args:
            archive_path: Path to the archive file to invalidate
        """
        cache_key = str(archive_path.absolute())
        
        with self._lock:
            if cache_key in self._handlers:
                handler = self._handlers[cache_key]
                try:
                    handler.close()
                except Exception:
                    pass
                del self._handlers[cache_key]
                del self._access_times[cache_key]
    
    def clear(self):
        """Clear all cached archives."""
        with self._lock:
            # Close all handlers
            for handler in self._handlers.values():
                try:
                    handler.close()
                except Exception:
                    pass
            
            # Clear caches
            self._handlers.clear()
            self._access_times.clear()
    
    def _evict_lru(self):
        """Evict the least recently used cache entry."""
        if not self._handlers:
            return
        
        # Find the entry with the oldest access time
        oldest_key = min(self._access_times.keys(), 
                        key=lambda k: self._access_times[k])
        
        # Close and remove the handler
        handler = self._handlers[oldest_key]
        try:
            handler.close()
        except Exception:
            pass
        
        del self._handlers[oldest_key]
        del self._access_times[oldest_key]
        self._evictions += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring.
        
        Returns:
            Dictionary containing cache statistics:
            - open_archives: Number of currently open archives
            - max_open: Maximum number of archives that can be open
            - ttl: Time-to-live in seconds
            - expired_count: Number of expired entries (not yet evicted)
            - cache_hits: Number of cache hits
            - cache_misses: Number of cache misses
            - hit_rate: Cache hit rate (0.0 to 1.0)
            - evictions: Number of LRU evictions performed
            - avg_open_time: Average time to open an archive (seconds)
        """
        with self._lock:
            current_time = time.time()
            expired_count = sum(
                1 for cache_key in self._access_times.keys()
                if current_time - self._access_times[cache_key] > self._ttl
            )
            
            total_requests = self._cache_hits + self._cache_misses
            hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0.0
            avg_open_time = self._total_open_time / self._cache_misses if self._cache_misses > 0 else 0.0
            
            return {
                'open_archives': len(self._handlers),
                'max_open': self._max_open,
                'ttl': self._ttl,
                'expired_count': expired_count,
                'cache_hits': self._cache_hits,
                'cache_misses': self._cache_misses,
                'hit_rate': hit_rate,
                'evictions': self._evictions,
                'avg_open_time': avg_open_time
            }


# Global archive cache instance
_archive_cache = None


def get_archive_cache() -> ArchiveCache:
    """Get or create the global archive cache instance."""
    global _archive_cache
    if _archive_cache is None:
        # Get configuration from config if available
        try:
            from tfm_config import get_config
            config = get_config()
            max_open = getattr(config, 'ARCHIVE_CACHE_MAX_OPEN', 5)
            ttl = getattr(config, 'ARCHIVE_CACHE_TTL', 300)
        except (ImportError, Exception):
            # Fallback to defaults
            max_open = 5
            ttl = 300
        
        _archive_cache = ArchiveCache(max_open=max_open, ttl=ttl)
    
    return _archive_cache


class ArchivePathImpl(PathImpl):
    """
    Archive file implementation of PathImpl.
    
    This class provides access to files and directories within archive files
    as if they were a virtual filesystem. Archive paths use the format:
    archive:///absolute/path/to/archive.zip#internal/path
    
    The '#' separator distinguishes the archive file path from the internal path.
    """
    
    def __init__(self, archive_uri: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize with archive URI and optional metadata.
        
        Args:
            archive_uri: URI in format archive://path/to/file.zip#internal/path
            metadata: Optional cached metadata to avoid archive reads
        """
        self._uri = archive_uri
        self._metadata = metadata or {}
        
        # Parse the URI to extract archive path and internal path
        self._parse_uri()
        
        # Get the global archive cache
        self._cache = get_archive_cache()
        
        # Cache for frequently accessed properties to avoid repeated computation
        self._property_cache = {}
    
    def _parse_uri(self):
        """Parse archive URI into archive path and internal path components."""
        if not self._uri.startswith('archive://'):
            raise ValueError(f"Invalid archive URI: {self._uri}")
        
        # Remove the 'archive://' prefix
        path_part = self._uri[10:]  # len('archive://') = 10
        
        # Split on '#' to separate archive path from internal path
        if '#' in path_part:
            archive_path_str, internal_path = path_part.split('#', 1)
        else:
            # No internal path specified, use root
            archive_path_str = path_part
            internal_path = ''
        
        # Create Path object for the archive file
        self._archive_path = Path(archive_path_str)
        
        # Normalize internal path
        self._internal_path = self._normalize_internal_path(internal_path)
    
    def _normalize_internal_path(self, path: str) -> str:
        """
        Normalize internal archive paths.
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized path (no leading slash, consistent separators)
        """
        # Remove leading/trailing slashes
        path = path.strip('/')
        # Normalize path separators
        path = path.replace('\\', '/')
        return path
    
    def _get_archive_handler(self) -> ArchiveHandler:
        """Get or create cached archive handler for this archive file."""
        return self._cache.get_handler(self._archive_path)
    
    def _get_entry(self) -> Optional[ArchiveEntry]:
        """Get the ArchiveEntry for this path."""
        # Check metadata cache first
        if 'entry' in self._metadata:
            return self._metadata['entry']
        
        # Get from archive handler
        handler = self._get_archive_handler()
        entry = handler.get_entry_info(self._internal_path)
        
        # Cache the entry
        if entry:
            self._metadata['entry'] = entry
        
        return entry
    
    def __str__(self) -> str:
        """String representation of the path."""
        return self._uri
    
    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if isinstance(other, ArchivePathImpl):
            return self._uri == other._uri
        elif isinstance(other, str):
            return self._uri == other
        return False
    
    def __hash__(self) -> int:
        """Hash support for use in sets and dicts."""
        return hash(self._uri)
    
    def __lt__(self, other) -> bool:
        """Less than comparison for sorting."""
        if isinstance(other, ArchivePathImpl):
            return self._uri < other._uri
        return self._uri < str(other)
    
    # Properties
    @property
    def name(self) -> str:
        """The final component of the path."""
        # Check property cache first
        if 'name' in self._property_cache:
            return self._property_cache['name']
        
        if not self._internal_path:
            # Root of archive - return archive filename
            result = self._archive_path.name
        else:
            # Return last component of internal path
            parts = self._internal_path.rstrip('/').split('/')
            result = parts[-1] if parts else ''
        
        self._property_cache['name'] = result
        return result
    
    @property
    def stem(self) -> str:
        """The final component without its suffix."""
        name = self.name
        if '.' in name:
            return name.rsplit('.', 1)[0]
        return name
    
    @property
    def suffix(self) -> str:
        """The file extension of the final component."""
        name = self.name
        if '.' in name:
            return '.' + name.rsplit('.', 1)[1]
        return ''
    
    @property
    def suffixes(self) -> List[str]:
        """A list of the path's suffixes."""
        name = self.name
        if '.' not in name:
            return []
        
        parts = name.split('.')
        return ['.' + part for part in parts[1:]]
    
    @property
    def parent(self) -> 'Path':
        """The logical parent of the path."""
        if not self._internal_path:
            # At root of archive - parent is the directory containing the archive
            return self._archive_path.parent
        
        # Get parent of internal path
        parts = self._internal_path.rstrip('/').split('/')
        if len(parts) > 1:
            parent_internal = '/'.join(parts[:-1])
        else:
            parent_internal = ''
        
        # Create new archive path for parent
        parent_uri = f"archive://{self._archive_path.absolute()}#{parent_internal}"
        return Path(parent_uri)
    
    @property
    def parents(self):
        """A sequence providing access to the logical ancestors of the path."""
        parents_list = []
        current = self.parent
        
        while True:
            parents_list.append(current)
            
            # Check if we've reached the archive root
            if isinstance(current._impl, ArchivePathImpl):
                if not current._impl._internal_path:
                    # At archive root, add the archive's parent directory
                    parents_list.append(current._impl._archive_path.parent)
                    break
                current = current.parent
            else:
                # Reached filesystem path
                break
        
        return parents_list
    
    @property
    def parts(self) -> tuple:
        """A tuple giving access to the path's components."""
        # Check property cache first
        if 'parts' in self._property_cache:
            return self._property_cache['parts']
        
        # Include archive path parts and internal path parts
        archive_parts = self._archive_path.parts
        
        if self._internal_path:
            internal_parts = tuple(self._internal_path.split('/'))
            result = archive_parts + ('#',) + internal_parts
        else:
            result = archive_parts + ('#',)
        
        self._property_cache['parts'] = result
        return result
    
    @property
    def anchor(self) -> str:
        """The concatenation of the drive and root."""
        return self._archive_path.anchor
    
    # Path manipulation methods
    def absolute(self) -> 'Path':
        """Return an absolute version of this path."""
        # Archive paths are always absolute
        abs_archive = self._archive_path.absolute()
        abs_uri = f"archive://{abs_archive}#{self._internal_path}"
        return Path(abs_uri)
    
    def resolve(self, strict: bool = False) -> 'Path':
        """Make the path absolute, resolving any symlinks."""
        # Archive paths don't have symlinks, just return absolute
        return self.absolute()
    
    def expanduser(self) -> 'Path':
        """Return a new path with expanded ~ and ~user constructs."""
        # Expand user in archive path
        expanded_archive = self._archive_path.expanduser()
        expanded_uri = f"archive://{expanded_archive}#{self._internal_path}"
        return Path(expanded_uri)
    
    def joinpath(self, *args) -> 'Path':
        """Combine this path with one or several arguments."""
        # Join to internal path
        if not args:
            return Path(self._uri)
        
        # Combine all arguments
        joined_parts = [self._internal_path] if self._internal_path else []
        for arg in args:
            arg_str = str(arg).strip('/')
            if arg_str:
                joined_parts.append(arg_str)
        
        new_internal = '/'.join(joined_parts)
        new_uri = f"archive://{self._archive_path.absolute()}#{new_internal}"
        return Path(new_uri)
    
    def with_name(self, name: str) -> 'Path':
        """Return a new path with the name changed."""
        if not self._internal_path:
            raise ValueError("Cannot change name of archive root")
        
        # Replace last component
        parts = self._internal_path.rstrip('/').split('/')
        parts[-1] = name
        new_internal = '/'.join(parts)
        new_uri = f"archive://{self._archive_path.absolute()}#{new_internal}"
        return Path(new_uri)
    
    def with_stem(self, stem: str) -> 'Path':
        """Return a new path with the stem changed."""
        suffix = self.suffix
        new_name = stem + suffix
        return self.with_name(new_name)
    
    def with_suffix(self, suffix: str) -> 'Path':
        """Return a new path with the suffix changed."""
        stem = self.stem
        new_name = stem + suffix
        return self.with_name(new_name)
    
    def relative_to(self, other) -> 'Path':
        """Return a version of this path relative to the other path."""
        # For archive paths, this is complex - simplified implementation
        if isinstance(other, Path) and isinstance(other._impl, ArchivePathImpl):
            other_impl = other._impl
            
            # Must be in same archive
            if self._archive_path != other_impl._archive_path:
                raise ValueError(f"{self} is not relative to {other}")
            
            # Get relative internal path
            if not other_impl._internal_path:
                # Other is archive root
                return Path(self._internal_path)
            
            # Check if self is under other
            if self._internal_path.startswith(other_impl._internal_path + '/'):
                rel_path = self._internal_path[len(other_impl._internal_path) + 1:]
                return Path(rel_path)
            
            raise ValueError(f"{self} is not relative to {other}")
        
        raise ValueError(f"{self} is not relative to {other}")
    
    # File system query methods
    def exists(self) -> bool:
        """Whether this path exists."""
        try:
            # Check if archive file exists
            if not self._archive_path.exists():
                return False
            
            # Root of archive always exists if archive exists
            if not self._internal_path:
                return True
            
            # Check if entry exists in archive
            entry = self._get_entry()
            return entry is not None
        except Exception:
            return False
    
    def is_dir(self) -> bool:
        """Whether this path is a directory."""
        try:
            # Root of archive is always a directory
            if not self._internal_path:
                return True
            
            entry = self._get_entry()
            return entry.is_dir if entry else False
        except Exception:
            return False
    
    def is_file(self) -> bool:
        """Whether this path is a regular file."""
        try:
            # Root of archive is not a file
            if not self._internal_path:
                return False
            
            entry = self._get_entry()
            return not entry.is_dir if entry else False
        except Exception:
            return False
    
    def is_symlink(self) -> bool:
        """Whether this path is a symbolic link."""
        # Archives don't support symlinks in our implementation
        return False
    
    def is_absolute(self) -> bool:
        """Whether this path is absolute."""
        # Archive paths are always absolute
        return True
    
    def stat(self):
        """Return the result of os.stat() on this path."""
        entry = self._get_entry()
        if not entry:
            raise FileNotFoundError(f"No such file or directory: {self}")
        
        return entry.to_stat_result()
    
    def lstat(self):
        """Return the result of os.lstat() on this path."""
        # No symlinks in archives, same as stat
        return self.stat()
    
    # Directory operations
    def iterdir(self) -> Iterator['Path']:
        """Iterate over the files in this directory."""
        if not self.is_dir():
            raise NotADirectoryError(f"Not a directory: {self}")
        
        try:
            handler = self._get_archive_handler()
            entries = handler.list_entries(self._internal_path)
            
            for entry in entries:
                entry_uri = f"archive://{self._archive_path.absolute()}#{entry.internal_path}"
                # Create Path with cached metadata
                path = Path(entry_uri)
                path._impl._metadata['entry'] = entry
                yield path
        except Exception as e:
            raise OSError(f"Error iterating directory: {e}")
    
    def glob(self, pattern: str) -> Iterator['Path']:
        """Iterate over this subtree and yield all existing files matching pattern."""
        if not self.is_dir():
            return
        
        # Handle ** pattern for recursive search
        if pattern.startswith('**/'):
            # Recursive pattern - search all subdirectories
            sub_pattern = pattern[3:]  # Remove **/ prefix
            
            # Yield matching items in current directory
            for item in self.iterdir():
                if fnmatch.fnmatch(item.name, sub_pattern):
                    yield item
                
                # Recursively search subdirectories
                if item.is_dir():
                    try:
                        for sub_item in item.glob(pattern):
                            yield sub_item
                    except Exception:
                        pass
        else:
            # Non-recursive pattern - only search current directory
            for item in self.iterdir():
                if fnmatch.fnmatch(item.name, pattern):
                    yield item
    
    def rglob(self, pattern: str) -> Iterator['Path']:
        """Recursively iterate over this subtree and yield all existing files matching pattern."""
        # rglob is like glob with ** prefix
        return self.glob(f"**/{pattern}")
    
    def match(self, pattern: str) -> bool:
        """Return True if this path matches the given pattern."""
        return fnmatch.fnmatch(str(self), pattern)
    
    # File I/O operations
    def open(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
        """Open the file pointed to by this path."""
        if 'w' in mode or 'a' in mode or '+' in mode:
            raise OSError("Archive files are read-only")
        
        if not self.is_file():
            raise IsADirectoryError(f"Is a directory: {self}")
        
        try:
            handler = self._get_archive_handler()
            data = handler.extract_to_bytes(self._internal_path)
            
            if 'b' in mode:
                # Binary mode
                return io.BytesIO(data)
            else:
                # Text mode
                text = data.decode(encoding or 'utf-8', errors or 'strict')
                return io.StringIO(text)
        except Exception as e:
            raise OSError(f"Error opening file: {e}")
    
    def read_text(self, encoding=None, errors=None) -> str:
        """Open the file in text mode, read it, and close the file."""
        try:
            handler = self._get_archive_handler()
            data = handler.extract_to_bytes(self._internal_path)
            return data.decode(encoding or 'utf-8', errors or 'strict')
        except Exception as e:
            raise OSError(f"Error reading text: {e}")
    
    def read_bytes(self) -> bytes:
        """Open the file in bytes mode, read it, and close the file."""
        try:
            handler = self._get_archive_handler()
            return handler.extract_to_bytes(self._internal_path)
        except Exception as e:
            raise OSError(f"Error reading bytes: {e}")
    
    def write_text(self, data: str, encoding=None, errors=None, newline=None) -> int:
        """Open the file in text mode, write to it, and close the file."""
        raise OSError("Archive files are read-only")
    
    def write_bytes(self, data: bytes) -> int:
        """Open the file in bytes mode, write to it, and close the file."""
        raise OSError("Archive files are read-only")
    
    # File system modification operations
    def mkdir(self, mode=0o777, parents=False, exist_ok=False):
        """Create a new directory at this given path."""
        raise OSError("Archive files are read-only")
    
    def rmdir(self):
        """Remove this directory."""
        raise OSError("Archive files are read-only")
    
    def unlink(self, missing_ok=False):
        """Remove this file or symbolic link."""
        raise OSError("Archive files are read-only")
    
    def rename(self, target) -> 'Path':
        """Rename this file or directory to the given target."""
        raise OSError("Archive files are read-only")
    
    def replace(self, target) -> 'Path':
        """Replace this file or directory with the given target."""
        raise OSError("Archive files are read-only")
    
    def symlink_to(self, target, target_is_directory=False):
        """Make this path a symlink pointing to the target path."""
        raise OSError("Archive files are read-only")
    
    def hardlink_to(self, target):
        """Make this path a hard link pointing to the same file as target."""
        raise OSError("Archive files are read-only")
    
    def touch(self, mode=0o666, exist_ok=True):
        """Create this file with the given access mode, if it doesn't exist."""
        raise OSError("Archive files are read-only")
    
    def chmod(self, mode):
        """Change the permissions of the path."""
        raise OSError("Archive files are read-only")
    
    # Storage-specific methods
    def is_remote(self) -> bool:
        """Return True if this path represents a remote resource."""
        # Archive paths are virtual, but the underlying archive might be remote
        return self._archive_path.is_remote()
    
    def get_scheme(self) -> str:
        """Return the scheme of the path (e.g., 'file', 's3', 'scp')."""
        return 'archive'
    
    def as_uri(self) -> str:
        """Return the path as a URI."""
        return self._uri
    
    def supports_directory_rename(self) -> bool:
        """Return True if this storage implementation supports directory renaming."""
        return False  # Archives are read-only
    
    def supports_file_editing(self) -> bool:
        """Return True if this storage implementation supports external editor editing (vim, nano, etc.)"""
        return False  # Archives are read-only
    
    def supports_write_operations(self) -> bool:
        """Return True if this storage implementation supports write operations (copy, move, create, delete)"""
        return False  # Archives are read-only
    
    # Display methods for UI presentation
    def get_display_prefix(self) -> str:
        """Return a prefix for display purposes.
        
        For archive entries, returns 'ARCHIVE: ' to indicate the storage type
        in UI components like text viewers and info dialogs.
        
        Returns:
            str: 'ARCHIVE: ' (with trailing space)
        """
        return 'ARCHIVE: '
    
    def get_display_title(self) -> str:
        """Return a formatted title for display in viewers and dialogs.
        
        For archive entries, returns the full archive URI which includes both
        the archive file path and the internal path within the archive.
        
        Returns:
            str: Full archive URI in format 'archive://path/to/file.zip#internal/path'
        """
        return self._uri
    
    # Content reading strategy methods
    def requires_extraction_for_reading(self) -> bool:
        """Return True if content must be extracted before reading.
        
        Archive files must be extracted from the archive container before their
        content can be read. This affects how content is accessed - it cannot be
        read directly and must be extracted to memory or disk first.
        
        Returns:
            bool: True - archive content always requires extraction
        """
        return True
    
    def supports_streaming_read(self) -> bool:
        """Return True if file can be read line-by-line without full extraction.
        
        Archive files do not support streaming reads. The entire file must be
        extracted from the archive before it can be accessed. This affects memory
        usage during operations like search, as the full content must be loaded.
        
        Returns:
            bool: False - archive content cannot be streamed
        """
        return False
    
    def get_search_strategy(self) -> str:
        """Return recommended search strategy for this storage type.
        
        Archive files require the 'extracted' strategy, meaning the entire file
        content must be extracted from the archive before searching can begin.
        This is necessary because archive formats don't support random access
        or streaming reads of individual files.
        
        Returns:
            str: 'extracted' - must extract entire content before searching
        """
        return 'extracted'
    
    def should_cache_for_search(self) -> bool:
        """Return True if content should be cached during search operations.
        
        Archive content should be cached during search operations because
        extraction is expensive. Caching the extracted content allows multiple
        search operations or result viewing without repeated extraction overhead.
        
        Returns:
            bool: True - caching is recommended for archive content
        """
        return True
    
    # Metadata method for info dialogs
    def get_extended_metadata(self) -> dict:
        """Return storage-specific metadata for display in info dialogs.
        
        For archive entries, provides detailed information including the archive
        file name, internal path within the archive, compressed and uncompressed
        sizes, compression type, and modification time.
        
        Returns:
            dict: Metadata dictionary with keys:
                - 'type': 'archive'
                - 'details': List of (label, value) tuples with archive-specific fields
                - 'format_hint': 'archive'
        """
        entry = self._get_entry()
        if not entry:
            # If entry doesn't exist, return minimal metadata
            details = [
                ('Archive', self._archive_path.name),
                ('Internal Path', self._internal_path or '/'),
                ('Type', 'Unknown'),
            ]
        else:
            details = [
                ('Archive', self._archive_path.name),
                ('Internal Path', self._internal_path or '/'),
                ('Type', 'Directory' if entry.is_dir else 'File'),
                ('Compressed Size', self._format_size(entry.compressed_size)),
                ('Uncompressed Size', self._format_size(entry.size)),
                ('Compression', self._get_compression_name(entry.archive_type)),
                ('Modified', self._format_archive_time(entry.mtime))
            ]
        
        return {
            'type': 'archive',
            'details': details,
            'format_hint': 'archive'
        }
    
    def _format_size(self, size: int) -> str:
        """Format size in human-readable format.
        
        Args:
            size: Size in bytes
            
        Returns:
            str: Formatted size string (e.g., '1.2 MB', '345 KB')
        """
        if size < 0:
            return '0 B'
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                if unit == 'B':
                    return f"{int(size)} {unit}"
                else:
                    return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def _get_compression_name(self, archive_type: str) -> str:
        """Convert archive type to compression name.
        
        Args:
            archive_type: Archive format string (e.g., 'zip', 'tar.gz', 'tar')
            
        Returns:
            str: Human-readable compression name
        """
        compression_map = {
            'zip': 'ZIP (Deflated)',
            'tar': 'None (Uncompressed)',
            'tar.gz': 'GZIP',
            'tar.bz2': 'BZIP2',
            'tar.xz': 'LZMA/XZ',
        }
        return compression_map.get(archive_type, archive_type.upper())
    
    def _format_archive_time(self, timestamp: float) -> str:
        """Format archive entry modification time.
        
        Args:
            timestamp: Unix timestamp (seconds since epoch)
            
        Returns:
            str: Formatted date/time string (e.g., '2024-01-15 10:30:00')
        """
        import datetime
        try:
            dt = datetime.datetime.fromtimestamp(timestamp)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, OSError):
            # Handle invalid timestamps
            return 'Unknown'
    
    # Compatibility methods
    def samefile(self, other_path) -> bool:
        """Return whether other_path is the same or not as this file."""
        if isinstance(other_path, Path) and isinstance(other_path._impl, ArchivePathImpl):
            return self._uri == other_path._impl._uri
        return False
    
    def as_posix(self) -> str:
        """Return the string representation with forward slashes."""
        return self._uri


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
        # Use module-level getLogger - no need to check if log_manager exists
        from tfm_log_manager import getLogger
        self.logger = getLogger("Archive")
        self.cache_manager = cache_manager
        self.progress_manager = progress_manager
    

    
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
            self.logger.info(f"Creating {format_type} archive: {archive_path}")
            
            # Determine format info
            format_info = None
            for ext, info in self.SUPPORTED_FORMATS.items():
                if ext.lstrip('.') == format_type or ext == f'.{format_type}':
                    format_info = info
                    break
            
            if not format_info:
                self.logger.error(f"Unsupported archive format: {format_type}")
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
            self.logger.error(f"Error creating archive: {e}")
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
                        self.logger.info(f"Added to archive: {arcname}")
            
            elif format_info['type'] == 'zip':
                with zipfile.ZipFile(str(archive_path), 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for source_path in source_paths:
                        if source_path.is_file():
                            zip_file.write(str(source_path), source_path.name)
                            self.logger.info(f"Added to archive: {source_path.name}")
                        elif source_path.is_dir():
                            # Add directory recursively
                            for file_path in source_path.rglob('*'):
                                if file_path.is_file():
                                    # Create relative path within the directory
                                    rel_path = file_path.relative_to(source_path.parent)
                                    zip_file.write(str(file_path), str(rel_path))
                                    self.logger.info(f"Added to archive: {rel_path}")
            
            else:
                self.logger.error(f"Unsupported archive type for local creation: {format_info['type']}")
                return False
            
            self.logger.info(f"Archive created successfully: {archive_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating local archive: {e}")
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
            
            # Create archive in temporary location
            temp_archive = temp_dir_path / f"archive{self._get_extension_for_format(format_info)}"
            success = self._create_archive_local(staged_paths, Path(temp_archive), format_info)
            
            if not success:
                return False
            
            # Upload/move archive to final destination
            if archive_path.is_remote():
                # Upload to remote storage
                archive_path.write_bytes(temp_archive.read_bytes())
                self.logger.info(f"Uploaded archive to: {archive_path}")
            else:
                # Move to local destination
                import shutil
                shutil.move(str(temp_archive), str(archive_path))
                self.logger.info(f"Moved archive to: {archive_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating cross-storage archive: {e}")
            return False
        
        finally:
            # Clean up temporary directory
            if temp_dir and PathlibPath(temp_dir).exists():
                import shutil
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    self.logger.warning(f"Warning: Could not clean up temp directory: {e}")
    
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
            self.logger.error(f"Error downloading directory {remote_dir}: {e}")
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
                self.logger.error(f"Archive file not found: {archive_path}")
                return False
            
            format_info = self.get_archive_format(archive_path.name)
            if not format_info:
                self.logger.error(f"Unsupported archive format: {archive_path.name}")
                return False
            
            self.logger.info(f"Extracting archive: {archive_path} to {destination_dir}")
            
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
            self.logger.error(f"Error extracting archive: {e}")
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
                                self.logger.warning(f"File exists, skipping: {member.name}")
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
                    
                    self.logger.info(f"Extracted {len(members_to_extract)} items")
            
            elif format_info['type'] == 'zip':
                with zipfile.ZipFile(str(archive_path), 'r') as zip_file:
                    members_to_extract = zip_file.namelist()
                    
                    # Check for overwrite conflicts and filter members
                    if not overwrite:
                        filtered_members = []
                        for member in members_to_extract:
                            dest_path = destination_dir / member
                            if dest_path.exists():
                                self.logger.warning(f"File exists, skipping: {member}")
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
                    
                    self.logger.info(f"Extracted {len(members_to_extract)} items")
            
            elif format_info['type'] in ['gzip', 'bzip2', 'xz']:
                # Single file compression
                output_name = archive_path.stem
                if archive_path.suffix in ['.gz', '.bz2', '.xz']:
                    output_name = archive_path.stem
                
                output_path = destination_dir / output_name
                
                if output_path.exists() and not overwrite:
                    self.logger.warning(f"File exists, not overwriting: {output_name}")
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
                
                self.logger.info(f"Decompressed to: {output_name}")
            
            else:
                self.logger.error(f"Unsupported archive type for local extraction: {format_info['type']}")
                return False
            
            self.logger.info(f"Archive extracted successfully to: {destination_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error extracting local archive: {e}")
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
                self.logger.info(f"Downloaded archive to temp: {archive_path.name}")
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
                self.logger.info(f"Uploaded extracted files to: {destination_dir}")
            else:
                # Move extracted files to local destination
                destination_dir.mkdir(parents=True, exist_ok=True)
                for item in temp_extract_dir.iterdir():
                    dest_item = destination_dir / item.name
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
                
                self.logger.info(f"Moved extracted files to: {destination_dir}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error extracting cross-storage archive: {e}")
            return False
        
        finally:
            # Clean up temporary directory
            if temp_dir and PathlibPath(temp_dir).exists():
                import shutil
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    self.logger.warning(f"Warning: Could not clean up temp directory: {e}")
    
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
                        self.logger.warning(f"Remote file exists, skipping: {item.name}")
                        continue
                    remote_item.write_bytes(item.read_bytes())
                elif item.is_dir():
                    if not remote_item.exists():
                        remote_item.mkdir(parents=True, exist_ok=True)
                    self._upload_directory_recursive(item, remote_item, overwrite)
        except Exception as e:
            self.logger.error(f"Error uploading directory {local_dir}: {e}")
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
            self.logger.error(f"Error listing archive contents: {e}")
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
                focused_file = current_pane['files'][current_pane['focused_index']]
                files_to_archive.append(focused_file)
        
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
        self.file_manager.quick_edit_bar.show_status_line_input(
            prompt="Archive filename: ",
            help_text="ESC:cancel Enter:create (.zip/.tar.gz/.tgz)",
            initial_text=default_filename,
            callback=self.on_create_archive_confirm,
            cancel_callback=self.on_create_archive_cancel
        )
        self.file_manager.mark_dirty()
        
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
            self.file_manager.quick_edit_bar.hide()
            self.file_manager.mark_dirty()
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
                focused_file = current_pane['files'][current_pane['focused_index']]
                files_to_archive.append(focused_file)
        
        if not files_to_archive:
            print("No files to archive")
            self.file_manager.quick_edit_bar.hide()
            self.file_manager.mark_dirty()
            return
        
        archive_filename = archive_name.strip()
        archive_path = other_pane['path'] / archive_filename
        
        # Check if archive already exists
        if archive_path.exists():
            print(f"Archive '{archive_filename}' already exists")
            self.file_manager.quick_edit_bar.hide()
            self.file_manager.mark_dirty()
            return
        
        try:
            # Determine archive format from filename
            format_type = self._get_archive_format_from_filename(archive_filename)
            
            if not format_type:
                print(f"Unsupported archive format. Supported: .zip, .tar.gz, .tar.bz2, .tar.xz, .tgz, .tbz2, .txz")
                self.file_manager.quick_edit_bar.hide()
                self.file_manager.mark_dirty()
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
                            other_pane['focused_index'] = i
                            self.file_manager.adjust_scroll_for_focus(other_pane)
                            break
                else:
                    print(f"Failed to create archive: {archive_filename}")
                    
            finally:
                self.progress_manager.finish_operation()
            
            self.file_manager.quick_edit_bar.hide()
            self.file_manager.mark_dirty()
            
        except Exception as e:
            print(f"Error creating archive: {e}")
            self.progress_manager.finish_operation()
            self.file_manager.quick_edit_bar.hide()
            self.file_manager.mark_dirty()
    
    def on_create_archive_cancel(self):
        """Handle create archive cancellation"""
        print("Archive creation cancelled")
        self.file_manager.quick_edit_bar.hide()
        self.file_manager.mark_dirty()
    
    def extract_selected_archive(self):
        """Extract the selected archive file to the other pane"""
        current_pane = self.file_manager.get_current_pane()
        other_pane = self.file_manager.get_inactive_pane()
        
        if not current_pane['files']:
            print("No files in current directory")
            return
        
        # Get the selected file
        focused_file = current_pane['files'][current_pane['focused_index']]
        
        if not focused_file.is_file():
            print("Focused item is not a file")
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
                    self.file_manager.mark_dirty()
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
        from tfm_quick_edit_bar import QuickEditBarHelpers
        QuickEditBarHelpers.create_rename_dialog(
            self.file_manager.quick_edit_bar,
            original_basename,
            original_basename
        )
        self.file_manager.quick_edit_bar.callback = self._on_extraction_rename_confirm
        self.file_manager.quick_edit_bar.cancel_callback = self._on_extraction_rename_cancel
        self.file_manager.mark_dirty()
    
    def _on_extraction_rename_confirm(self, new_name):
        """Handle extraction rename confirmation"""
        if not new_name or new_name.strip() == "":
            print("Extraction cancelled: empty directory name")
            self.file_manager.quick_edit_bar.hide()
            self.file_manager.mark_dirty()
            return
        
        context = self.file_manager._extraction_rename_context
        archive_file = context['archive_file']
        other_pane = context['other_pane']
        original_basename = context['original_basename']
        new_name = new_name.strip()
        new_extract_dir = other_pane['path'] / new_name
        
        # Hide the dialog first
        self.file_manager.quick_edit_bar.hide()
        self.file_manager.mark_dirty()
        
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
        self.file_manager.quick_edit_bar.hide()
        self.file_manager.mark_dirty()
    
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
        # Mark as needing redraw to show progress
        # Note: Don't call renderer.refresh() here - UILayerStack will do it
        try:
            self.file_manager.draw_status()
            self.file_manager.mark_dirty()
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