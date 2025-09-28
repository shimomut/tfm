#!/usr/bin/env python3
"""
TFM Path - A pathlib-compatible Path class that can be extended for remote storage support
"""

import os
import stat
import fnmatch
from abc import ABC, abstractmethod
from pathlib import Path as PathlibPath, PurePath
from datetime import datetime
from typing import Union, Iterator, List, Optional, Any


class PathImpl(ABC):
    """
    Abstract base class for path implementations.
    
    This defines the interface that all storage implementations must provide.
    Subclasses implement specific storage backends (local, S3, SCP, etc.).
    """
    
    @abstractmethod
    def __str__(self) -> str:
        """String representation of the path"""
        pass
    
    @abstractmethod
    def __eq__(self, other) -> bool:
        """Equality comparison"""
        pass
    
    @abstractmethod
    def __hash__(self) -> int:
        """Hash support for use in sets and dicts"""
        pass
    
    @abstractmethod
    def __lt__(self, other) -> bool:
        """Less than comparison for sorting"""
        pass
    
    # Properties
    @property
    @abstractmethod
    def name(self) -> str:
        """The final component of the path"""
        pass
    
    @property
    @abstractmethod
    def stem(self) -> str:
        """The final component without its suffix"""
        pass
    
    @property
    @abstractmethod
    def suffix(self) -> str:
        """The file extension of the final component"""
        pass
    
    @property
    @abstractmethod
    def suffixes(self) -> List[str]:
        """A list of the path's suffixes"""
        pass
    
    @property
    @abstractmethod
    def parent(self) -> 'Path':
        """The logical parent of the path"""
        pass
    
    @property
    @abstractmethod
    def parents(self):
        """A sequence providing access to the logical ancestors of the path"""
        pass
    
    @property
    @abstractmethod
    def parts(self) -> tuple:
        """A tuple giving access to the path's components"""
        pass
    
    @property
    @abstractmethod
    def anchor(self) -> str:
        """The concatenation of the drive and root"""
        pass
    
    # Path manipulation methods
    @abstractmethod
    def absolute(self) -> 'Path':
        """Return an absolute version of this path"""
        pass
    
    @abstractmethod
    def resolve(self, strict: bool = False) -> 'Path':
        """Make the path absolute, resolving any symlinks"""
        pass
    
    @abstractmethod
    def expanduser(self) -> 'Path':
        """Return a new path with expanded ~ and ~user constructs"""
        pass
    
    @abstractmethod
    def joinpath(self, *args) -> 'Path':
        """Combine this path with one or several arguments"""
        pass
    
    @abstractmethod
    def with_name(self, name: str) -> 'Path':
        """Return a new path with the name changed"""
        pass
    
    @abstractmethod
    def with_stem(self, stem: str) -> 'Path':
        """Return a new path with the stem changed"""
        pass
    
    @abstractmethod
    def with_suffix(self, suffix: str) -> 'Path':
        """Return a new path with the suffix changed"""
        pass
    
    @abstractmethod
    def relative_to(self, other) -> 'Path':
        """Return a version of this path relative to the other path"""
        pass
    
    # File system query methods
    @abstractmethod
    def exists(self) -> bool:
        """Whether this path exists"""
        pass
    
    @abstractmethod
    def is_dir(self) -> bool:
        """Whether this path is a directory"""
        pass
    
    @abstractmethod
    def is_file(self) -> bool:
        """Whether this path is a regular file"""
        pass
    
    @abstractmethod
    def is_symlink(self) -> bool:
        """Whether this path is a symbolic link"""
        pass
    
    @abstractmethod
    def is_absolute(self) -> bool:
        """Whether this path is absolute"""
        pass
    
    @abstractmethod
    def stat(self):
        """Return the result of os.stat() on this path"""
        pass
    
    @abstractmethod
    def lstat(self):
        """Return the result of os.lstat() on this path"""
        pass
    
    # Directory operations
    @abstractmethod
    def iterdir(self) -> Iterator['Path']:
        """Iterate over the files in this directory"""
        pass
    
    @abstractmethod
    def glob(self, pattern: str) -> Iterator['Path']:
        """Iterate over this subtree and yield all existing files matching pattern"""
        pass
    
    @abstractmethod
    def rglob(self, pattern: str) -> Iterator['Path']:
        """Recursively iterate over this subtree and yield all existing files matching pattern"""
        pass
    
    @abstractmethod
    def match(self, pattern: str) -> bool:
        """Return True if this path matches the given pattern"""
        pass
    
    # File I/O operations
    @abstractmethod
    def open(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
        """Open the file pointed to by this path"""
        pass
    
    @abstractmethod
    def read_text(self, encoding=None, errors=None) -> str:
        """Open the file in text mode, read it, and close the file"""
        pass
    
    @abstractmethod
    def read_bytes(self) -> bytes:
        """Open the file in bytes mode, read it, and close the file"""
        pass
    
    @abstractmethod
    def write_text(self, data: str, encoding=None, errors=None, newline=None) -> int:
        """Open the file in text mode, write to it, and close the file"""
        pass
    
    @abstractmethod
    def write_bytes(self, data: bytes) -> int:
        """Open the file in bytes mode, write to it, and close the file"""
        pass
    
    # File system modification operations
    @abstractmethod
    def mkdir(self, mode=0o777, parents=False, exist_ok=False):
        """Create a new directory at this given path"""
        pass
    
    @abstractmethod
    def rmdir(self):
        """Remove this directory"""
        pass
    
    @abstractmethod
    def unlink(self, missing_ok=False):
        """Remove this file or symbolic link"""
        pass
    
    @abstractmethod
    def rename(self, target) -> 'Path':
        """Rename this file or directory to the given target"""
        pass
    
    @abstractmethod
    def replace(self, target) -> 'Path':
        """Replace this file or directory with the given target"""
        pass
    
    @abstractmethod
    def symlink_to(self, target, target_is_directory=False):
        """Make this path a symlink pointing to the target path"""
        pass
    
    @abstractmethod
    def hardlink_to(self, target):
        """Make this path a hard link pointing to the same file as target"""
        pass
    
    @abstractmethod
    def touch(self, mode=0o666, exist_ok=True):
        """Create this file with the given access mode, if it doesn't exist"""
        pass
    
    @abstractmethod
    def chmod(self, mode):
        """Change the permissions of the path"""
        pass
    
    # Storage-specific methods
    @abstractmethod
    def is_remote(self) -> bool:
        """Return True if this path represents a remote resource"""
        pass
    
    @abstractmethod
    def get_scheme(self) -> str:
        """Return the scheme of the path (e.g., 'file', 's3', 'scp')"""
        pass
    
    @abstractmethod
    def as_uri(self) -> str:
        """Return the path as a URI"""
        pass
    
    # Compatibility methods
    @abstractmethod
    def samefile(self, other_path) -> bool:
        """Return whether other_path is the same or not as this file"""
        pass
    
    @abstractmethod
    def as_posix(self) -> str:
        """Return the string representation with forward slashes"""
        pass


class LocalPathImpl(PathImpl):
    """
    Local file system implementation of PathImpl.
    
    This class wraps pathlib.Path to provide local file system operations
    while implementing the PathImpl interface.
    """
    
    def __init__(self, path_obj: PathlibPath):
        """Initialize with a pathlib.Path object"""
        self._path = path_obj
    
    def __str__(self) -> str:
        """String representation of the path"""
        return str(self._path)
    
    def __eq__(self, other) -> bool:
        """Equality comparison"""
        if isinstance(other, LocalPathImpl):
            return self._path == other._path
        elif isinstance(other, PathlibPath):
            return self._path == other
        elif isinstance(other, str):
            return str(self._path) == other
        return False
    
    def __hash__(self) -> int:
        """Hash support for use in sets and dicts"""
        return hash(self._path)
    
    def __lt__(self, other) -> bool:
        """Less than comparison for sorting"""
        if isinstance(other, LocalPathImpl):
            return str(self._path) < str(other._path)
        return str(self._path) < str(other)
    
    # Properties
    @property
    def name(self) -> str:
        """The final component of the path"""
        return self._path.name
    
    @property
    def stem(self) -> str:
        """The final component without its suffix"""
        return self._path.stem
    
    @property
    def suffix(self) -> str:
        """The file extension of the final component"""
        return self._path.suffix
    
    @property
    def suffixes(self) -> List[str]:
        """A list of the path's suffixes"""
        return self._path.suffixes
    
    @property
    def parent(self) -> 'Path':
        """The logical parent of the path"""
        return Path(self._path.parent)
    
    @property
    def parents(self):
        """A sequence providing access to the logical ancestors of the path"""
        return [Path(p) for p in self._path.parents]
    
    @property
    def parts(self) -> tuple:
        """A tuple giving access to the path's components"""
        return self._path.parts
    
    @property
    def anchor(self) -> str:
        """The concatenation of the drive and root"""
        return self._path.anchor
    
    # Path manipulation methods
    def absolute(self) -> 'Path':
        """Return an absolute version of this path"""
        return Path(self._path.absolute())
    
    def resolve(self, strict: bool = False) -> 'Path':
        """Make the path absolute, resolving any symlinks"""
        return Path(self._path.resolve(strict=strict))
    
    def expanduser(self) -> 'Path':
        """Return a new path with expanded ~ and ~user constructs"""
        return Path(self._path.expanduser())
    
    def joinpath(self, *args) -> 'Path':
        """Combine this path with one or several arguments"""
        return Path(self._path.joinpath(*args))
    
    def with_name(self, name: str) -> 'Path':
        """Return a new path with the name changed"""
        return Path(self._path.with_name(name))
    
    def with_stem(self, stem: str) -> 'Path':
        """Return a new path with the stem changed"""
        return Path(self._path.with_stem(stem))
    
    def with_suffix(self, suffix: str) -> 'Path':
        """Return a new path with the suffix changed"""
        return Path(self._path.with_suffix(suffix))
    
    def relative_to(self, other) -> 'Path':
        """Return a version of this path relative to the other path"""
        if isinstance(other, Path):
            other = other._impl._path
        elif isinstance(other, LocalPathImpl):
            other = other._path
        return Path(self._path.relative_to(other))
    
    # File system query methods
    def exists(self) -> bool:
        """Whether this path exists"""
        return self._path.exists()
    
    def is_dir(self) -> bool:
        """Whether this path is a directory"""
        return self._path.is_dir()
    
    def is_file(self) -> bool:
        """Whether this path is a regular file"""
        return self._path.is_file()
    
    def is_symlink(self) -> bool:
        """Whether this path is a symbolic link"""
        return self._path.is_symlink()
    
    def is_absolute(self) -> bool:
        """Whether this path is absolute"""
        return self._path.is_absolute()
    
    def stat(self):
        """Return the result of os.stat() on this path"""
        return self._path.stat()
    
    def lstat(self):
        """Return the result of os.lstat() on this path"""
        return self._path.lstat()
    
    # Directory operations
    def iterdir(self) -> Iterator['Path']:
        """Iterate over the files in this directory"""
        for item in self._path.iterdir():
            yield Path(item)
    
    def glob(self, pattern: str) -> Iterator['Path']:
        """Iterate over this subtree and yield all existing files matching pattern"""
        for item in self._path.glob(pattern):
            yield Path(item)
    
    def rglob(self, pattern: str) -> Iterator['Path']:
        """Recursively iterate over this subtree and yield all existing files matching pattern"""
        for item in self._path.rglob(pattern):
            yield Path(item)
    
    def match(self, pattern: str) -> bool:
        """Return True if this path matches the given pattern"""
        return self._path.match(pattern)
    
    # File I/O operations
    def open(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
        """Open the file pointed to by this path"""
        return self._path.open(mode, buffering, encoding, errors, newline)
    
    def read_text(self, encoding=None, errors=None) -> str:
        """Open the file in text mode, read it, and close the file"""
        return self._path.read_text(encoding, errors)
    
    def read_bytes(self) -> bytes:
        """Open the file in bytes mode, read it, and close the file"""
        return self._path.read_bytes()
    
    def write_text(self, data: str, encoding=None, errors=None, newline=None) -> int:
        """Open the file in text mode, write to it, and close the file"""
        return self._path.write_text(data, encoding, errors, newline)
    
    def write_bytes(self, data: bytes) -> int:
        """Open the file in bytes mode, write to it, and close the file"""
        return self._path.write_bytes(data)
    
    # File system modification operations
    def mkdir(self, mode=0o777, parents=False, exist_ok=False):
        """Create a new directory at this given path"""
        return self._path.mkdir(mode, parents, exist_ok)
    
    def rmdir(self):
        """Remove this directory"""
        return self._path.rmdir()
    
    def unlink(self, missing_ok=False):
        """Remove this file or symbolic link"""
        return self._path.unlink(missing_ok)
    
    def rename(self, target) -> 'Path':
        """Rename this file or directory to the given target"""
        if isinstance(target, Path):
            target = target._impl._path
        elif isinstance(target, LocalPathImpl):
            target = target._path
        return Path(self._path.rename(target))
    
    def replace(self, target) -> 'Path':
        """Replace this file or directory with the given target"""
        if isinstance(target, Path):
            target = target._impl._path
        elif isinstance(target, LocalPathImpl):
            target = target._path
        return Path(self._path.replace(target))
    
    def symlink_to(self, target, target_is_directory=False):
        """Make this path a symlink pointing to the target path"""
        if isinstance(target, Path):
            target = target._impl._path
        elif isinstance(target, LocalPathImpl):
            target = target._path
        return self._path.symlink_to(target, target_is_directory)
    
    def hardlink_to(self, target):
        """Make this path a hard link pointing to the same file as target"""
        if isinstance(target, Path):
            target = target._impl._path
        elif isinstance(target, LocalPathImpl):
            target = target._path
        return self._path.hardlink_to(target)
    
    def touch(self, mode=0o666, exist_ok=True):
        """Create this file with the given access mode, if it doesn't exist"""
        return self._path.touch(mode, exist_ok)
    
    def chmod(self, mode):
        """Change the permissions of the path"""
        return self._path.chmod(mode)
    
    # Storage-specific methods
    def is_remote(self) -> bool:
        """Return True if this path represents a remote resource"""
        return False
    
    def get_scheme(self) -> str:
        """Return the scheme of the path (e.g., 'file', 's3', 'scp')"""
        return 'file'
    
    def as_uri(self) -> str:
        """Return the path as a URI"""
        return self._path.as_uri()
    
    # Compatibility methods
    def samefile(self, other_path) -> bool:
        """Return whether other_path is the same or not as this file"""
        if isinstance(other_path, Path):
            other_path = other_path._impl._path
        elif isinstance(other_path, LocalPathImpl):
            other_path = other_path._path
        return self._path.samefile(other_path)
    
    def as_posix(self) -> str:
        """Return the string representation with forward slashes"""
        return self._path.as_posix()


class Path:
    """
    A pathlib-compatible Path class designed to support both local and remote storage.
    
    This class acts as a facade that delegates operations to specific storage
    implementations (LocalPathImpl, S3PathImpl, etc.) based on the path scheme.
    """
    
    def __init__(self, *args):
        """Initialize Path with the same interface as pathlib.Path"""
        # Determine the appropriate implementation based on the path
        if len(args) == 1 and isinstance(args[0], Path):
            # Copy constructor
            self._impl = args[0]._impl
        elif len(args) == 1 and isinstance(args[0], PathlibPath):
            # Wrap existing pathlib.Path
            self._impl = LocalPathImpl(args[0])
        else:
            # Create new path from string arguments
            path_str = str(PathlibPath(*args))
            self._impl = self._create_implementation(path_str)
    
    def _create_implementation(self, path_str: str) -> PathImpl:
        """Create the appropriate implementation based on the path string"""
        # For now, all paths are local. Future versions will detect schemes
        # like s3://, scp://, etc. and create appropriate implementations
        return LocalPathImpl(PathlibPath(path_str))
    
    def __str__(self):
        """String representation of the path"""
        return str(self._impl)
    
    def __repr__(self):
        """Representation of the path"""
        return f"Path({str(self._impl)!r})"
    
    def __fspath__(self):
        """Support for os.fspath()"""
        return str(self._impl)
    
    def __truediv__(self, other):
        """Support for / operator"""
        return self._impl.joinpath(other)
    
    def __rtruediv__(self, other):
        """Support for reverse / operator"""
        return Path(other) / self
    
    def __eq__(self, other):
        """Equality comparison"""
        if isinstance(other, Path):
            return self._impl == other._impl
        else:
            return self._impl == other
    
    def __hash__(self):
        """Hash support for use in sets and dicts"""
        return hash(self._impl)
    
    def __lt__(self, other):
        """Less than comparison for sorting"""
        if isinstance(other, Path):
            return self._impl < other._impl
        return self._impl < other
    
    # Properties that delegate to implementation
    @property
    def name(self) -> str:
        """The final component of the path"""
        return self._impl.name
    
    @property
    def stem(self) -> str:
        """The final component without its suffix"""
        return self._impl.stem
    
    @property
    def suffix(self) -> str:
        """The file extension of the final component"""
        return self._impl.suffix
    
    @property
    def suffixes(self) -> List[str]:
        """A list of the path's suffixes"""
        return self._impl.suffixes
    
    @property
    def parent(self) -> 'Path':
        """The logical parent of the path"""
        return self._impl.parent
    
    @property
    def parents(self):
        """A sequence providing access to the logical ancestors of the path"""
        return self._impl.parents
    
    @property
    def parts(self) -> tuple:
        """A tuple giving access to the path's components"""
        return self._impl.parts
    
    @property
    def anchor(self) -> str:
        """The concatenation of the drive and root"""
        return self._impl.anchor
    
    # Methods that delegate to implementation
    def absolute(self) -> 'Path':
        """Return an absolute version of this path"""
        return self._impl.absolute()
    
    def resolve(self, strict: bool = False) -> 'Path':
        """Make the path absolute, resolving any symlinks"""
        return self._impl.resolve(strict=strict)
    
    def expanduser(self) -> 'Path':
        """Return a new path with expanded ~ and ~user constructs"""
        return self._impl.expanduser()
    
    def exists(self) -> bool:
        """Whether this path exists"""
        return self._impl.exists()
    
    def is_dir(self) -> bool:
        """Whether this path is a directory"""
        return self._impl.is_dir()
    
    def is_file(self) -> bool:
        """Whether this path is a regular file"""
        return self._impl.is_file()
    
    def is_symlink(self) -> bool:
        """Whether this path is a symbolic link"""
        return self._impl.is_symlink()
    
    def is_absolute(self) -> bool:
        """Whether this path is absolute"""
        return self._impl.is_absolute()
    
    def stat(self):
        """Return the result of os.stat() on this path"""
        return self._impl.stat()
    
    def lstat(self):
        """Return the result of os.lstat() on this path"""
        return self._impl.lstat()
    
    def iterdir(self) -> Iterator['Path']:
        """Iterate over the files in this directory"""
        return self._impl.iterdir()
    
    def glob(self, pattern: str) -> Iterator['Path']:
        """Iterate over this subtree and yield all existing files matching pattern"""
        return self._impl.glob(pattern)
    
    def rglob(self, pattern: str) -> Iterator['Path']:
        """Recursively iterate over this subtree and yield all existing files matching pattern"""
        return self._impl.rglob(pattern)
    
    def match(self, pattern: str) -> bool:
        """Return True if this path matches the given pattern"""
        return self._impl.match(pattern)
    
    def relative_to(self, other) -> 'Path':
        """Return a version of this path relative to the other path"""
        return self._impl.relative_to(other)
    
    def with_name(self, name: str) -> 'Path':
        """Return a new path with the name changed"""
        return self._impl.with_name(name)
    
    def with_stem(self, stem: str) -> 'Path':
        """Return a new path with the stem changed"""
        return self._impl.with_stem(stem)
    
    def with_suffix(self, suffix: str) -> 'Path':
        """Return a new path with the suffix changed"""
        return self._impl.with_suffix(suffix)
    
    def joinpath(self, *args) -> 'Path':
        """Combine this path with one or several arguments"""
        return self._impl.joinpath(*args)
    
    # File operations
    def open(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
        """Open the file pointed to by this path"""
        return self._impl.open(mode, buffering, encoding, errors, newline)
    
    def read_text(self, encoding=None, errors=None) -> str:
        """Open the file in text mode, read it, and close the file"""
        return self._impl.read_text(encoding, errors)
    
    def read_bytes(self) -> bytes:
        """Open the file in bytes mode, read it, and close the file"""
        return self._impl.read_bytes()
    
    def write_text(self, data: str, encoding=None, errors=None, newline=None) -> int:
        """Open the file in text mode, write to it, and close the file"""
        return self._impl.write_text(data, encoding, errors, newline)
    
    def write_bytes(self, data: bytes) -> int:
        """Open the file in bytes mode, write to it, and close the file"""
        return self._impl.write_bytes(data)
    
    # Directory operations
    def mkdir(self, mode=0o777, parents=False, exist_ok=False):
        """Create a new directory at this given path"""
        return self._impl.mkdir(mode, parents, exist_ok)
    
    def rmdir(self):
        """Remove this directory"""
        return self._impl.rmdir()
    
    def unlink(self, missing_ok=False):
        """Remove this file or symbolic link"""
        return self._impl.unlink(missing_ok)
    
    def rename(self, target) -> 'Path':
        """Rename this file or directory to the given target"""
        return self._impl.rename(target)
    
    def replace(self, target) -> 'Path':
        """Replace this file or directory with the given target"""
        return self._impl.replace(target)
    
    def symlink_to(self, target, target_is_directory=False):
        """Make this path a symlink pointing to the target path"""
        return self._impl.symlink_to(target, target_is_directory)
    
    def hardlink_to(self, target):
        """Make this path a hard link pointing to the same file as target"""
        return self._impl.hardlink_to(target)
    
    def touch(self, mode=0o666, exist_ok=True):
        """Create this file with the given access mode, if it doesn't exist"""
        return self._impl.touch(mode, exist_ok)
    
    def chmod(self, mode):
        """Change the permissions of the path"""
        return self._impl.chmod(mode)
    
    # Class methods
    @classmethod
    def cwd(cls) -> 'Path':
        """Return a new path representing the current working directory"""
        return cls(PathlibPath.cwd())
    
    @classmethod
    def home(cls) -> 'Path':
        """Return a new path representing the user's home directory"""
        return cls(PathlibPath.home())
    
    # Storage-specific methods
    def is_remote(self) -> bool:
        """Return True if this path represents a remote resource"""
        return self._impl.is_remote()
    
    def get_scheme(self) -> str:
        """Return the scheme of the path (e.g., 'file', 's3', 'scp')"""
        return self._impl.get_scheme()
    
    def as_uri(self) -> str:
        """Return the path as a URI"""
        return self._impl.as_uri()
    
    # Compatibility methods for os.path operations
    def samefile(self, other_path) -> bool:
        """Return whether other_path is the same or not as this file"""
        return self._impl.samefile(other_path)
    
    def as_posix(self) -> str:
        """Return the string representation with forward slashes"""
        return self._impl.as_posix()


# Convenience functions that mirror pathlib module-level functions
def PurePath(*args):
    """Create a PurePath - for now, just return our Path class"""
    return Path(*args)


# For backward compatibility, provide access to the underlying pathlib Path
def as_pathlib_path(path: Path) -> PathlibPath:
    """Convert our Path back to a pathlib.Path if needed"""
    if isinstance(path, Path) and isinstance(path._impl, LocalPathImpl):
        return path._impl._path
    return path