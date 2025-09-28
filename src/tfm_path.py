#!/usr/bin/env python3
"""
TFM Path - A pathlib-compatible Path class that can be extended for remote storage support
"""

import os
import stat
import fnmatch
from pathlib import Path as PathlibPath, PurePath
from datetime import datetime
from typing import Union, Iterator, List, Optional, Any


class Path:
    """
    A pathlib-compatible Path class designed to support both local and remote storage.
    
    This class wraps pathlib.Path for local operations but provides an interface
    that can be extended to support remote storage systems like S3, SCP, etc.
    """
    
    def __init__(self, *args):
        """Initialize Path with the same interface as pathlib.Path"""
        if len(args) == 1 and isinstance(args[0], (Path, PathlibPath)):
            # Handle Path-like objects
            if isinstance(args[0], Path):
                self._path = args[0]._path
            else:
                self._path = args[0]
        else:
            # Handle string paths and multiple arguments
            self._path = PathlibPath(*args)
    
    def __str__(self):
        """String representation of the path"""
        return str(self._path)
    
    def __repr__(self):
        """Representation of the path"""
        return f"Path({str(self._path)!r})"
    
    def __fspath__(self):
        """Support for os.fspath()"""
        return str(self._path)
    
    def __truediv__(self, other):
        """Support for / operator"""
        return Path(self._path / other)
    
    def __rtruediv__(self, other):
        """Support for reverse / operator"""
        return Path(other) / self
    
    def __eq__(self, other):
        """Equality comparison"""
        if isinstance(other, Path):
            return self._path == other._path
        elif isinstance(other, PathlibPath):
            return self._path == other
        elif isinstance(other, str):
            return str(self._path) == other
        return False
    
    def __hash__(self):
        """Hash support for use in sets and dicts"""
        return hash(self._path)
    
    def __lt__(self, other):
        """Less than comparison for sorting"""
        if isinstance(other, Path):
            return str(self._path) < str(other._path)
        return str(self._path) < str(other)
    
    # Properties that mirror pathlib.Path
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
    
    # Methods that mirror pathlib.Path
    def absolute(self) -> 'Path':
        """Return an absolute version of this path"""
        return Path(self._path.absolute())
    
    def resolve(self, strict: bool = False) -> 'Path':
        """Make the path absolute, resolving any symlinks"""
        return Path(self._path.resolve(strict=strict))
    
    def expanduser(self) -> 'Path':
        """Return a new path with expanded ~ and ~user constructs"""
        return Path(self._path.expanduser())
    
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
    
    def relative_to(self, other) -> 'Path':
        """Return a version of this path relative to the other path"""
        if isinstance(other, Path):
            other = other._path
        return Path(self._path.relative_to(other))
    
    def with_name(self, name: str) -> 'Path':
        """Return a new path with the name changed"""
        return Path(self._path.with_name(name))
    
    def with_stem(self, stem: str) -> 'Path':
        """Return a new path with the stem changed"""
        return Path(self._path.with_stem(stem))
    
    def with_suffix(self, suffix: str) -> 'Path':
        """Return a new path with the suffix changed"""
        return Path(self._path.with_suffix(suffix))
    
    def joinpath(self, *args) -> 'Path':
        """Combine this path with one or several arguments"""
        return Path(self._path.joinpath(*args))
    
    # File operations
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
    
    # Directory operations
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
            target = target._path
        return Path(self._path.rename(target))
    
    def replace(self, target) -> 'Path':
        """Replace this file or directory with the given target"""
        if isinstance(target, Path):
            target = target._path
        return Path(self._path.replace(target))
    
    def symlink_to(self, target, target_is_directory=False):
        """Make this path a symlink pointing to the target path"""
        if isinstance(target, Path):
            target = target._path
        return self._path.symlink_to(target, target_is_directory)
    
    def hardlink_to(self, target):
        """Make this path a hard link pointing to the same file as target"""
        if isinstance(target, Path):
            target = target._path
        return self._path.hardlink_to(target)
    
    def touch(self, mode=0o666, exist_ok=True):
        """Create this file with the given access mode, if it doesn't exist"""
        return self._path.touch(mode, exist_ok)
    
    def chmod(self, mode):
        """Change the permissions of the path"""
        return self._path.chmod(mode)
    
    # Class methods
    @classmethod
    def cwd(cls) -> 'Path':
        """Return a new path representing the current working directory"""
        return cls(PathlibPath.cwd())
    
    @classmethod
    def home(cls) -> 'Path':
        """Return a new path representing the user's home directory"""
        return cls(PathlibPath.home())
    
    # Additional methods for future remote storage support
    def is_remote(self) -> bool:
        """Return True if this path represents a remote resource"""
        # For now, all paths are local
        return False
    
    def get_scheme(self) -> str:
        """Return the scheme of the path (e.g., 'file', 's3', 'scp')"""
        # For now, all paths are local files
        return 'file'
    
    def as_uri(self) -> str:
        """Return the path as a URI"""
        return self._path.as_uri()
    
    # Compatibility methods for os.path operations
    def samefile(self, other_path) -> bool:
        """Return whether other_path is the same or not as this file"""
        if isinstance(other_path, Path):
            other_path = other_path._path
        return self._path.samefile(other_path)
    
    def as_posix(self) -> str:
        """Return the string representation with forward slashes"""
        return self._path.as_posix()


# Convenience functions that mirror pathlib module-level functions
def PurePath(*args):
    """Create a PurePath - for now, just return our Path class"""
    return Path(*args)


# For backward compatibility, provide access to the underlying pathlib Path
def as_pathlib_path(path: Path) -> PathlibPath:
    """Convert our Path back to a pathlib.Path if needed"""
    if isinstance(path, Path):
        return path._path
    return path