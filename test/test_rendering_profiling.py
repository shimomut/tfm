"""
Integration tests for rendering profiling functionality.

Tests that rendering operations are profiled when profiling mode is enabled.

Run with: PYTHONPATH=.:src:ttk pytest test/test_rendering_profiling.py -v
"""

import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from tfm_profiling import ProfilingManager


def test_rendering_profiling_creates_profile_file(tmp_path):
    """Test that rendering profiling creates a profile file"""
    output_dir = str(tmp_path / "profiling_output")
    
    # Create profiling manager with profiling enabled (profile all renders)
    manager = ProfilingManager(enabled=True, output_dir=output_dir, render_profile_interval=0)
    
    # Create a mock rendering function
    def mock_render():
        """Mock rendering function that does some work"""
        total = 0
        for i in range(1000):
            total += i
        return total
    
    # Profile the rendering function
    result = manager.profile_rendering(mock_render)
    
    # Verify the function executed
    assert result == sum(range(1000))
    
    # Wait for async file write to complete
    time.sleep(0.1)
    
    # Verify profile file was created
    profile_files = list(Path(output_dir).glob("render_profile_*.prof"))
    assert len(profile_files) == 1, f"Expected 1 profile file, found {len(profile_files)}"
    
    # Verify profile file has content
    profile_file = profile_files[0]
    assert profile_file.stat().st_size > 0, "Profile file is empty"
    
    print(f"✓ Rendering profiling created profile file: {profile_file.name}")


def test_rendering_profiling_with_arguments(tmp_path):
    """Test that rendering profiling works with function arguments"""
    output_dir = str(tmp_path / "profiling_output_args")
    
    # Create profiling manager with profiling enabled (profile all renders)
    manager = ProfilingManager(enabled=True, output_dir=output_dir, render_profile_interval=0)
    
    # Create a mock rendering function with arguments
    def mock_render_with_args(width, height, color="blue"):
        """Mock rendering function with arguments"""
        return f"Rendered {width}x{height} in {color}"
    
    # Profile the rendering function with arguments
    result = manager.profile_rendering(mock_render_with_args, 800, 600, color="red")
    
    # Verify the function executed with correct arguments
    assert result == "Rendered 800x600 in red"
    
    # Wait for async file write to complete
    time.sleep(0.1)
    
    # Verify profile file was created
    profile_files = list(Path(output_dir).glob("render_profile_*.prof"))
    assert len(profile_files) == 1
    
    print("✓ Rendering profiling works with function arguments")


def test_rendering_profiling_disabled(tmp_path):
    """Test that rendering profiling does nothing when disabled"""
    output_dir = str(tmp_path / "profiling_output_disabled")
    
    # Create profiling manager with profiling disabled
    manager = ProfilingManager(enabled=False, output_dir=output_dir)
    
    # Create a mock rendering function
    def mock_render():
        return "rendered"
    
    # Profile the rendering function (should do nothing)
    result = manager.profile_rendering(mock_render)
    
    # Verify the function executed
    assert result == "rendered"
    
    # Verify no profile files were created
    if Path(output_dir).exists():
        profile_files = list(Path(output_dir).glob("render_profile_*.prof"))
        assert len(profile_files) == 0, "Profile files should not be created when profiling is disabled"
    
    print("✓ Rendering profiling does nothing when disabled")


def test_rendering_profiling_multiple_calls(tmp_path):
    """Test that multiple rendering calls create multiple profile files"""
    output_dir = str(tmp_path / "profiling_output_multiple")
    
    # Create profiling manager with profiling enabled (profile all renders)
    manager = ProfilingManager(enabled=True, output_dir=output_dir, render_profile_interval=0)
    
    # Create a mock rendering function
    def mock_render(frame_num):
        """Mock rendering function"""
        return f"frame_{frame_num}"
    
    # Profile multiple rendering calls
    for i in range(3):
        result = manager.profile_rendering(mock_render, i)
        assert result == f"frame_{i}"
        time.sleep(0.01)  # Small delay to ensure unique timestamps
    
    # Wait for async file writes to complete
    time.sleep(0.2)
    
    # Verify multiple profile files were created
    profile_files = list(Path(output_dir).glob("render_profile_*.prof"))
    assert len(profile_files) == 3, f"Expected 3 profile files, found {len(profile_files)}"
    
    # Verify all files have unique names
    filenames = [f.name for f in profile_files]
    assert len(filenames) == len(set(filenames)), "Profile filenames should be unique"
    
    print(f"✓ Multiple rendering calls created {len(profile_files)} unique profile files")


def test_rendering_profiling_filename_format(tmp_path):
    """Test that rendering profile filenames follow the expected format"""
    output_dir = str(tmp_path / "profiling_output_format")
    
    # Create profiling manager with profiling enabled (profile all renders)
    manager = ProfilingManager(enabled=True, output_dir=output_dir, render_profile_interval=0)
    
    # Create a mock rendering function
    def mock_render():
        return "rendered"
    
    # Profile the rendering function
    manager.profile_rendering(mock_render)
    
    # Wait for async file write to complete
    time.sleep(0.1)
    
    # Verify profile file follows naming convention
    profile_files = list(Path(output_dir).glob("render_profile_*.prof"))
    assert len(profile_files) == 1
    
    filename = profile_files[0].name
    
    # Check filename format: render_profile_YYYYMMDD_HHMMSS_microseconds.prof
    assert filename.startswith("render_profile_"), "Filename should start with 'render_profile_'"
    assert filename.endswith(".prof"), "Filename should end with '.prof'"
    
    # Extract timestamp part
    timestamp_part = filename[len("render_profile_"):-len(".prof")]
    parts = timestamp_part.split("_")
    
    # Should have 3 parts: date, time, microseconds
    assert len(parts) == 3, f"Expected 3 timestamp parts, got {len(parts)}"
    
    # Verify date format (YYYYMMDD)
    assert len(parts[0]) == 8, "Date should be 8 digits (YYYYMMDD)"
    assert parts[0].isdigit(), "Date should be all digits"
    
    # Verify time format (HHMMSS)
    assert len(parts[1]) == 6, "Time should be 6 digits (HHMMSS)"
    assert parts[1].isdigit(), "Time should be all digits"
    
    # Verify microseconds format
    assert len(parts[2]) == 6, "Microseconds should be 6 digits"
    assert parts[2].isdigit(), "Microseconds should be all digits"
    
    print(f"✓ Rendering profile filename follows expected format: {filename}")


def test_rendering_profiling_output_directory_creation(tmp_path):
    """Test that rendering profiling creates output directory if it doesn't exist"""
    output_dir = str(tmp_path / "new_profiling_output")
    
    # Verify directory doesn't exist yet
    assert not Path(output_dir).exists()
    
    # Create profiling manager with profiling enabled (profile all renders)
    manager = ProfilingManager(enabled=True, output_dir=output_dir, render_profile_interval=0)
    
    # Create a mock rendering function
    def mock_render():
        return "rendered"
    
    # Profile the rendering function
    manager.profile_rendering(mock_render)
    
    # Wait for async file write to complete
    time.sleep(0.1)
    
    # Verify directory was created
    assert Path(output_dir).exists(), "Output directory should be created"
    assert Path(output_dir).is_dir(), "Output path should be a directory"
    
    # Verify README was created
    readme_path = Path(output_dir) / "README.txt"
    assert readme_path.exists(), "README.txt should be created"
    
    print(f"✓ Rendering profiling created output directory: {output_dir}")


def test_rendering_profiling_counter_increments(tmp_path):
    """Test that render profile counter increments correctly"""
    output_dir = str(tmp_path / "profiling_output_counter")
    
    # Create profiling manager with profiling enabled (profile all renders)
    manager = ProfilingManager(enabled=True, output_dir=output_dir, render_profile_interval=0)
    
    # Initial counter should be 0
    assert manager.render_profile_count == 0
    
    # Create a mock rendering function
    def mock_render():
        return "rendered"
    
    # Profile rendering multiple times
    for i in range(5):
        manager.profile_rendering(mock_render)
        time.sleep(0.01)  # Small delay for unique timestamps
    
    # Wait for async file writes to complete
    time.sleep(0.3)
    
    # Verify counter incremented
    assert manager.render_profile_count == 5, f"Expected counter to be 5, got {manager.render_profile_count}"
    
    print(f"✓ Render profile counter incremented correctly: {manager.render_profile_count}")


def run_all_tests():
    """Run all rendering profiling tests"""
    import tempfile
    
    print("=" * 70)
    print("Running Rendering Profiling Integration Tests")
    print("=" * 70)
    print()
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        try:
            test_rendering_profiling_creates_profile_file(tmp_path)
            test_rendering_profiling_with_arguments(tmp_path)
            test_rendering_profiling_disabled(tmp_path)
            test_rendering_profiling_multiple_calls(tmp_path)
            test_rendering_profiling_filename_format(tmp_path)
            test_rendering_profiling_output_directory_creation(tmp_path)
            test_rendering_profiling_counter_increments(tmp_path)
            
            print()
            print("=" * 70)
            print("All Rendering Profiling Tests Passed!")
            print("=" * 70)
            
        except AssertionError as e:
            print()
            print("=" * 70)
            print(f"Test Failed: {e}")
            print("=" * 70)
            sys.exit(1)
        except Exception as e:
            print()
            print("=" * 70)
            print(f"Unexpected Error: {e}")
            print("=" * 70)
            import traceback
            traceback.print_exc()
            sys.exit(1)
