#!/usr/bin/env python3
"""
TFM Cache Manager - Handles cache invalidation for file operations

This module provides cache invalidation functionality for TFM operations,
particularly for S3 storage where caching is used to improve performance.
"""

from typing import List, Optional
from tfm_path import Path


class CacheManager:
    """Manages cache invalidation for file operations across different storage types"""
    
    def __init__(self, log_manager=None):
        """Initialize cache manager with optional logging"""
        self.log_manager = log_manager
        # Use module-level getLogger - no need to check if log_manager exists
        from tfm_log_manager import getLogger
        self.logger = getLogger("Cache")

    
    def invalidate_cache_for_paths(self, paths: List[Path], operation: str = "operation"):
        """
        Invalidate cache for the given paths and their parent directories
        
        Args:
            paths: List of paths that were affected by an operation
            operation: Description of the operation for logging
        """
        if not paths:
            return
        
        # Group paths by storage scheme for efficient processing
        s3_paths = []
        
        for path in paths:
            if path.get_scheme() == 's3':
                s3_paths.append(path)
        
        # Invalidate S3 cache if needed
        if s3_paths:
            self._invalidate_s3_cache(s3_paths, operation)
    
    def _invalidate_s3_cache(self, s3_paths: List[Path], operation: str):
        """Invalidate S3 cache for the given paths"""
        try:
            # Import S3 cache here to avoid circular imports
            from tfm_s3 import get_s3_cache
            
            s3_cache = get_s3_cache()
            
            # Group paths by bucket for efficient invalidation
            buckets_to_invalidate = {}
            
            for path in s3_paths:
                if hasattr(path._impl, '_bucket') and hasattr(path._impl, '_key'):
                    bucket = path._impl._bucket
                    key = path._impl._key
                    
                    if bucket not in buckets_to_invalidate:
                        buckets_to_invalidate[bucket] = set()
                    
                    # Add the key itself
                    buckets_to_invalidate[bucket].add(key)
                    
                    # Add parent directory keys for directory listing invalidation
                    if key and '/' in key:
                        # Add all parent directory prefixes
                        key_parts = key.rstrip('/').split('/')
                        for i in range(len(key_parts)):
                            parent_prefix = '/'.join(key_parts[:i+1])
                            if parent_prefix:
                                buckets_to_invalidate[bucket].add(parent_prefix + '/')
                    
                    # Add bucket root for top-level changes
                    if not key or '/' not in key.strip('/'):
                        buckets_to_invalidate[bucket].add('')
            
            # Perform cache invalidation
            for bucket, keys in buckets_to_invalidate.items():
                for key in keys:
                    s3_cache.invalidate_key(bucket, key)
                    self.logger.debug(f"Invalidated S3 cache for {operation}: s3://{bucket}/{key}")
            
            if buckets_to_invalidate:
                self.logger.debug(f"S3 cache invalidation completed for {operation} on {len(s3_paths)} paths")
        
        except Exception as e:
            self.logger.warning(f"Warning: S3 cache invalidation failed for {operation}: {e}")
    
    def invalidate_cache_for_directory(self, directory: Path, operation: str = "operation"):
        """
        Invalidate cache for a directory and its parent directories
        
        Args:
            directory: Directory path that was affected
            operation: Description of the operation for logging
        """
        self.invalidate_cache_for_paths([directory], operation)
    
    def invalidate_cache_for_copy_operation(self, source_paths: List[Path], destination_dir: Path):
        """
        Invalidate cache for copy operations
        
        Args:
            source_paths: List of source paths that were copied
            destination_dir: Destination directory where files were copied
        """
        # Invalidate destination directory cache
        paths_to_invalidate = [destination_dir]
        
        # For each copied file, also invalidate the specific destination path
        for source_path in source_paths:
            dest_path = destination_dir / source_path.name
            paths_to_invalidate.append(dest_path)
        
        self.invalidate_cache_for_paths(paths_to_invalidate, "copy operation")
    
    def invalidate_cache_for_move_operation(self, source_paths: List[Path], destination_dir: Path):
        """
        Invalidate cache for move operations
        
        Args:
            source_paths: List of source paths that were moved
            destination_dir: Destination directory where files were moved
        """
        # Invalidate both source and destination caches
        paths_to_invalidate = [destination_dir]
        
        # Add source parent directories
        for source_path in source_paths:
            source_parent = source_path.parent
            if source_parent not in paths_to_invalidate:
                paths_to_invalidate.append(source_parent)
            
            # Add destination path
            dest_path = destination_dir / source_path.name
            paths_to_invalidate.append(dest_path)
        
        self.invalidate_cache_for_paths(paths_to_invalidate, "move operation")
    
    def invalidate_cache_for_delete_operation(self, deleted_paths: List[Path]):
        """
        Invalidate cache for delete operations
        
        Args:
            deleted_paths: List of paths that were deleted
        """
        # Invalidate parent directories of deleted files
        parent_dirs = set()
        
        for deleted_path in deleted_paths:
            parent_dir = deleted_path.parent
            parent_dirs.add(parent_dir)
            
            # Also invalidate the deleted path itself
            parent_dirs.add(deleted_path)
        
        self.invalidate_cache_for_paths(list(parent_dirs), "delete operation")
    
    def invalidate_cache_for_archive_operation(self, archive_path: Path, source_paths: List[Path] = None):
        """
        Invalidate cache for archive operations (creation/extraction)
        
        Args:
            archive_path: Path to the archive file that was created/extracted
            source_paths: Optional list of source paths that were archived
        """
        paths_to_invalidate = [archive_path, archive_path.parent]
        
        # If source paths provided, also invalidate their parent directories
        if source_paths:
            for source_path in source_paths:
                parent_dir = source_path.parent
                if parent_dir not in paths_to_invalidate:
                    paths_to_invalidate.append(parent_dir)
        
        self.invalidate_cache_for_paths(paths_to_invalidate, "archive operation")
    
    def invalidate_cache_for_create_operation(self, created_path: Path):
        """
        Invalidate cache for file/directory creation operations
        
        Args:
            created_path: Path that was created
        """
        paths_to_invalidate = [created_path, created_path.parent]
        self.invalidate_cache_for_paths(paths_to_invalidate, "create operation")