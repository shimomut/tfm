#!/usr/bin/env python3
"""
Property-Based Test for S3 Backend Consistency

**Feature: qt-gui-port, Property 25: S3 backend consistency**
**Validates: Requirements 9.3**

This test verifies that both TUI and GUI modes use the same S3 backend
implementation for file operations.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from tfm_s3 import S3PathImpl, HAS_BOTO3
    from tfm_path import Path as TFMPath
except ImportError:
    pytest.skip("S3 support not available", allow_module_level=True)


# Skip all tests if boto3 is not available
pytestmark = pytest.mark.skipif(not HAS_BOTO3, reason="boto3 not installed")


class TestS3BackendConsistency:
    """
    Property-based tests for S3 backend consistency between TUI and GUI modes.
    
    These tests verify that both modes use the same S3PathImpl implementation
    and that S3 operations behave identically regardless of UI mode.
    """
    
    @given(
        bucket_name=st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), min_codepoint=97, max_codepoint=122),
            min_size=3,
            max_size=20
        ),
        key_path=st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), min_codepoint=97, max_codepoint=122) | st.just('/'),
            min_size=1,
            max_size=50
        )
    )
    @settings(max_examples=100)
    def test_s3_path_implementation_is_shared(self, bucket_name, key_path):
        """
        Property 25: S3 backend consistency
        
        For any S3 URI, creating a Path object should use the same S3PathImpl
        implementation regardless of how it's created.
        
        This ensures both TUI and GUI modes use the same backend.
        """
        # Clean up key path to be valid
        key_path = key_path.strip('/').replace('//', '/')
        assume(len(key_path) > 0)
        assume(not key_path.startswith('-'))  # S3 keys can't start with dash
        
        # Create S3 URI
        s3_uri = f"s3://{bucket_name}/{key_path}"
        
        # Create Path object (this is how both TUI and GUI create paths)
        path_obj = TFMPath(s3_uri)
        
        # Verify it uses S3PathImpl
        assert hasattr(path_obj, '_impl'), "Path object should have _impl attribute"
        assert isinstance(path_obj._impl, S3PathImpl), \
            f"S3 paths should use S3PathImpl, got {type(path_obj._impl)}"
        
        # Verify the implementation has correct attributes
        assert hasattr(path_obj._impl, '_bucket'), "S3PathImpl should have _bucket"
        assert hasattr(path_obj._impl, '_key'), "S3PathImpl should have _key"
        assert path_obj._impl._bucket == bucket_name, "Bucket name should match"
        assert path_obj._impl._key == key_path, "Key path should match"
    
    @given(
        bucket_name=st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), min_codepoint=97, max_codepoint=122),
            min_size=3,
            max_size=20
        ),
        key_path=st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), min_codepoint=97, max_codepoint=122) | st.just('/'),
            min_size=1,
            max_size=50
        )
    )
    @settings(max_examples=100)
    def test_s3_scheme_detection_is_consistent(self, bucket_name, key_path):
        """
        Property 25: S3 backend consistency
        
        For any S3 path, the scheme detection should be consistent.
        Both TUI and GUI modes should identify S3 paths the same way.
        """
        # Clean up key path
        key_path = key_path.strip('/').replace('//', '/')
        assume(len(key_path) > 0)
        assume(not key_path.startswith('-'))
        
        # Create S3 URI
        s3_uri = f"s3://{bucket_name}/{key_path}"
        
        # Create Path object
        path_obj = TFMPath(s3_uri)
        
        # Verify scheme detection
        assert path_obj.get_scheme() == 's3', \
            f"S3 paths should have scheme 's3', got {path_obj.get_scheme()}"
        
        # Verify is_remote returns True
        assert path_obj.is_remote() == True, \
            "S3 paths should be identified as remote"
        
        # Verify as_uri returns the original URI
        assert path_obj.as_uri() == s3_uri, \
            f"as_uri() should return original URI, got {path_obj.as_uri()}"
    
    @given(
        bucket_name=st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), min_codepoint=97, max_codepoint=122),
            min_size=3,
            max_size=20
        ),
        key_path=st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), min_codepoint=97, max_codepoint=122) | st.just('/'),
            min_size=1,
            max_size=50
        )
    )
    @settings(max_examples=100)
    def test_s3_path_properties_are_consistent(self, bucket_name, key_path):
        """
        Property 25: S3 backend consistency
        
        For any S3 path, the path properties (name, parent, etc.) should be
        computed consistently using the same implementation.
        """
        # Clean up key path
        key_path = key_path.strip('/').replace('//', '/')
        assume(len(key_path) > 0)
        assume(not key_path.startswith('-'))
        assume('/' in key_path)  # Need at least one level for parent test
        
        # Create S3 URI
        s3_uri = f"s3://{bucket_name}/{key_path}"
        
        # Create Path object
        path_obj = TFMPath(s3_uri)
        
        # Test name property
        expected_name = key_path.rstrip('/').split('/')[-1]
        assert path_obj.name == expected_name, \
            f"Name should be {expected_name}, got {path_obj.name}"
        
        # Test parent property
        parent = path_obj.parent
        assert isinstance(parent._impl, S3PathImpl), \
            "Parent should also use S3PathImpl"
        assert parent._impl._bucket == bucket_name, \
            "Parent should have same bucket"
        
        # Test that parent's key is a prefix of child's key
        parent_key = parent._impl._key.rstrip('/')
        child_key = path_obj._impl._key.rstrip('/')
        if parent_key:  # Not at bucket root
            assert child_key.startswith(parent_key), \
                f"Child key {child_key} should start with parent key {parent_key}"
    
    @given(
        bucket_name=st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), min_codepoint=97, max_codepoint=122),
            min_size=3,
            max_size=20
        ),
        key_path=st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), min_codepoint=97, max_codepoint=122) | st.just('/'),
            min_size=1,
            max_size=50
        )
    )
    @settings(max_examples=100)
    def test_s3_cache_is_shared(self, bucket_name, key_path):
        """
        Property 25: S3 backend consistency
        
        For any S3 path, the cache should be shared across all S3PathImpl instances.
        This ensures consistent caching behavior in both TUI and GUI modes.
        """
        # Clean up key path
        key_path = key_path.strip('/').replace('//', '/')
        assume(len(key_path) > 0)
        assume(not key_path.startswith('-'))
        
        # Create two S3 path objects with the same URI
        s3_uri = f"s3://{bucket_name}/{key_path}"
        path_obj1 = TFMPath(s3_uri)
        path_obj2 = TFMPath(s3_uri)
        
        # Both should use S3PathImpl
        assert isinstance(path_obj1._impl, S3PathImpl)
        assert isinstance(path_obj2._impl, S3PathImpl)
        
        # Both should access the same cache instance
        cache1 = path_obj1._impl._cache
        cache2 = path_obj2._impl._cache
        
        # The cache instances should be the same object (singleton pattern)
        assert cache1 is cache2, \
            "All S3PathImpl instances should share the same cache"
    
    def test_s3_operations_use_same_implementation(self):
        """
        Property 25: S3 backend consistency
        
        Verify that S3 file operations use the same S3PathImpl implementation
        regardless of how they're invoked.
        
        This is a concrete test (not property-based) that verifies the
        implementation is consistent.
        """
        # Create an S3 path
        s3_uri = "s3://test-bucket/test-key.txt"
        path_obj = TFMPath(s3_uri)
        
        # Verify it uses S3PathImpl
        assert isinstance(path_obj._impl, S3PathImpl), \
            "S3 paths should use S3PathImpl"
        
        # Verify the implementation has the expected methods
        required_methods = [
            'exists', 'is_dir', 'is_file', 'stat', 'iterdir',
            'open', 'read_text', 'write_text', 'unlink', 'mkdir',
            'get_scheme', 'is_remote', 'as_uri'
        ]
        
        for method_name in required_methods:
            assert hasattr(path_obj._impl, method_name), \
                f"S3PathImpl should have {method_name} method"
            assert callable(getattr(path_obj._impl, method_name)), \
                f"S3PathImpl.{method_name} should be callable"
    
    def test_s3_directory_rename_restriction_is_consistent(self):
        """
        Property 25: S3 backend consistency
        
        Verify that S3 directory rename restrictions are consistently enforced
        in both TUI and GUI modes.
        """
        # Create an S3 directory path
        s3_uri = "s3://test-bucket/test-dir/"
        path_obj = TFMPath(s3_uri)
        
        # Verify it uses S3PathImpl
        assert isinstance(path_obj._impl, S3PathImpl)
        
        # Verify directory rename is not supported
        assert path_obj.supports_directory_rename() == False, \
            "S3 should not support directory renaming"
    
    def test_s3_file_editing_restriction_is_consistent(self):
        """
        Property 25: S3 backend consistency
        
        Verify that S3 file editing restrictions are consistently enforced
        in both TUI and GUI modes.
        """
        # Create an S3 file path
        s3_uri = "s3://test-bucket/test-file.txt"
        path_obj = TFMPath(s3_uri)
        
        # Verify it uses S3PathImpl
        assert isinstance(path_obj._impl, S3PathImpl)
        
        # Verify file editing is not supported
        assert path_obj.supports_file_editing() == False, \
            "S3 should not support in-place file editing"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
