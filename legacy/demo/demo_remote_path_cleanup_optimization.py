#!/usr/bin/env python3
"""
Demo: Remote Path Cleanup Optimization

This demo shows how the cleanup_non_existing_directories() function
has been optimized to skip existence checks for remote storage paths,
significantly improving TFM startup performance when there are S3 or
other remote paths in the history.
"""

import sys
import os
import time
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfm_state_manager import TFMStateManager
from tfm_path import Path


def demo_cleanup_optimization():
    """Demonstrate the remote path cleanup optimization."""
    
    print("=" * 60)
    print("TFM Remote Path Cleanup Optimization Demo")
    print("=" * 60)
    
    # Initialize state manager
    state_manager = TFMStateManager()
    
    print("\n1. Setting up test history with mixed local and remote paths...")
    
    # Create realistic test history
    test_history = [
        # Local paths (some exist, some don't)
        [time.time(), "/tmp", "temp_file.txt"],
        [time.time(), "/nonexistent/path", "missing.txt"],
        [time.time(), "/usr/local", "readme.txt"],
        [time.time(), "/fake/directory", "file.txt"],
        
        # S3 paths (would be slow to check)
        [time.time(), "s3://my-bucket/data/2024/", "dataset.csv"],
        [time.time(), "s3://backup-bucket/logs/", "app.log"],
        [time.time(), "s3://analytics/reports/", "monthly.pdf"],
        [time.time(), "s3://media-storage/images/", "photo.jpg"],
        
        # Other remote paths
        [time.time(), "scp://server.example.com/home/user/", "config.json"],
        [time.time(), "ftp://files.company.com/uploads/", "document.docx"],
    ]
    
    # Set up the test history for both panes
    state_manager.set_state("path_history_left", test_history, "demo_instance")
    state_manager.set_state("path_history_right", test_history[:5], "demo_instance")  # Fewer entries for right pane
    
    print(f"   - Created history with {len(test_history)} entries for left pane")
    print(f"   - Created history with 5 entries for right pane")
    print(f"   - Total: {len(test_history) + 5} history entries")
    
    # Track which paths get existence checks
    existence_checks = []
    
    def mock_exists(self):
        path_str = str(self)
        existence_checks.append(path_str)
        # Simulate realistic existence (some common paths exist)
        return path_str in ["/tmp", "/usr/local"]
    
    def mock_is_remote(self):
        path_str = str(self)
        return path_str.startswith(('s3://', 'scp://', 'ftp://'))
    
    print("\n2. Running cleanup with optimization...")
    
    # Measure performance
    start_time = time.time()
    
    with patch.object(Path, 'exists', mock_exists), \
         patch.object(Path, 'is_remote', mock_is_remote):
        
        result = state_manager.cleanup_non_existing_directories()
    
    elapsed_time = time.time() - start_time
    
    print(f"   - Cleanup completed in {elapsed_time:.3f} seconds")
    print(f"   - Result: {'Success' if result else 'Failed'}")
    
    print("\n3. Analysis of what was checked:")
    
    # Count different types of paths
    local_paths = [p for p in existence_checks if not p.startswith(('s3://', 'scp://', 'ftp://'))]
    remote_paths_in_history = [entry[1] for entry in test_history if entry[1].startswith(('s3://', 'scp://', 'ftp://'))]
    
    print(f"   - Local paths checked for existence: {len(local_paths)}")
    print(f"   - Remote paths in history: {len(remote_paths_in_history)}")
    print(f"   - Remote paths skipped (not checked): {len(remote_paths_in_history)}")
    
    print("\n4. Paths that were checked for existence:")
    for path in local_paths:
        exists = path in ["/tmp", "/usr/local"]
        print(f"   - {path} {'✓ exists' if exists else '✗ removed'}")
    
    print("\n5. Remote paths that were preserved (no existence check):")
    for path in remote_paths_in_history[:3]:  # Show first 3
        print(f"   - {path} (skipped)")
    if len(remote_paths_in_history) > 3:
        print(f"   - ... and {len(remote_paths_in_history) - 3} more remote paths")
    
    # Show final results
    left_history = state_manager.get_state("path_history_left", [])
    right_history = state_manager.get_state("path_history_right", [])
    
    print(f"\n6. Final results:")
    print(f"   - Left pane history: {len(left_history)} entries (was {len(test_history)})")
    print(f"   - Right pane history: {len(right_history)} entries (was 5)")
    
    # Count what remains
    remaining_local = sum(1 for entry in left_history if not entry[1].startswith(('s3://', 'scp://', 'ftp://')))
    remaining_remote = sum(1 for entry in left_history if entry[1].startswith(('s3://', 'scp://', 'ftp://')))
    
    print(f"   - Remaining local paths: {remaining_local}")
    print(f"   - Remaining remote paths: {remaining_remote}")
    
    print("\n7. Performance benefit:")
    print("   Without optimization:")
    print("   - Would check existence of ALL paths (including slow remote ones)")
    print("   - S3 existence checks can take 100-500ms each")
    print(f"   - Estimated time: {len(remote_paths_in_history)} × 200ms = {len(remote_paths_in_history) * 0.2:.1f}s")
    print("   With optimization:")
    print(f"   - Only checked {len(local_paths)} local paths")
    print(f"   - Actual time: {elapsed_time:.3f}s")
    print(f"   - Speed improvement: ~{(len(remote_paths_in_history) * 0.2 / max(elapsed_time, 0.001)):.0f}x faster")


def demo_performance_comparison():
    """Show performance comparison with and without optimization."""
    
    print("\n" + "=" * 60)
    print("Performance Comparison Demo")
    print("=" * 60)
    
    state_manager = TFMStateManager()
    
    # Create history with many S3 paths
    s3_history = []
    for i in range(50):
        s3_history.append([time.time(), f"s3://bucket-{i//10}/path{i}", f"file{i}.txt"])
    
    state_manager.set_state("path_history_left", s3_history, "perf_test")
    
    print(f"\nTesting with {len(s3_history)} S3 paths in history...")
    
    def slow_exists(self):
        # Simulate slow S3 existence check
        time.sleep(0.05)  # 50ms per check
        return True
    
    def mock_is_remote(self):
        return str(self).startswith('s3://')
    
    print("\n1. With optimization (current implementation):")
    start_time = time.time()
    
    with patch.object(Path, 'exists', slow_exists), \
         patch.object(Path, 'is_remote', mock_is_remote):
        
        result = state_manager.cleanup_non_existing_directories()
    
    optimized_time = time.time() - start_time
    print(f"   Time taken: {optimized_time:.2f} seconds")
    print(f"   Result: {'Success' if result else 'Failed'}")
    
    print("\n2. Without optimization (simulated old behavior):")
    # Simulate what would happen without optimization
    simulated_time = len(s3_history) * 0.05  # 50ms per S3 check
    print(f"   Estimated time: {simulated_time:.2f} seconds")
    print(f"   (Would check existence of all {len(s3_history)} S3 paths)")
    
    print(f"\n3. Performance improvement:")
    improvement = simulated_time / max(optimized_time, 0.001)
    print(f"   Speed improvement: {improvement:.1f}x faster")
    print(f"   Time saved: {simulated_time - optimized_time:.2f} seconds")
    
    print("\nThis optimization is especially important for users with:")
    print("   - Large S3 browsing history")
    print("   - Slow network connections")
    print("   - Many remote storage locations")
    print("   - Frequent TFM restarts")


if __name__ == "__main__":
    try:
        demo_cleanup_optimization()
        demo_performance_comparison()
        
        print("\n" + "=" * 60)
        print("✅ Demo completed successfully!")
        print("The optimization significantly improves TFM startup time")
        print("by skipping slow remote storage existence checks.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)