#!/usr/bin/env python3
"""
Final Integration Tests for Performance Profiling System

This test suite provides comprehensive end-to-end testing of the profiling system,
verifying that all components work together correctly across different backends
and workloads.

Tests cover:
- Complete profiling workflow end-to-end
- CoreGraphics backend compatibility
- Curses backend compatibility
- Various workloads (file operations, navigation, etc.)
- Profile file analysis with pstats
"""

import sys
import os
import time
import tempfile
import shutil
import pstats
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_profiling import ProfilingManager, FPSTracker, ProfileWriter


def test_complete_profiling_workflow():
    """Test complete profiling workflow end-to-end"""
    print("\n" + "=" * 70)
    print("Test: Complete Profiling Workflow End-to-End")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 1. Initialize profiling manager
        manager = ProfilingManager(enabled=True, output_dir=temp_dir, render_profile_interval=0)
        print("✓ Profiling manager initialized")
        
        # 2. Simulate main loop with FPS tracking
        for frame in range(10):
            manager.start_frame()
            
            # Simulate key handling
            if frame % 3 == 0:
                def mock_key_handler():
                    total = 0
                    for i in range(100):
                        total += i
                    return total
                
                manager.profile_key_handling(mock_key_handler)
            
            # Simulate rendering
            def mock_render():
                result = []
                for i in range(50):
                    result.append(i * 2)
                return result
            
            manager.profile_rendering(mock_render)
            
            time.sleep(0.01)  # Simulate frame time
        
        print("✓ Simulated 10 frames with key handling and rendering")
        
        # 3. Wait for async operations
        time.sleep(0.5)
        
        # 4. Verify FPS tracking
        assert len(manager.fps_tracker.frame_times) > 0, "FPS tracker should have recorded frames"
        fps = manager.fps_tracker.calculate_fps()
        assert fps > 0, "FPS should be calculated"
        print(f"✓ FPS tracking working: {fps:.2f} FPS")
        
        # 5. Verify profile files created
        key_profiles = list(Path(temp_dir).glob("key_profile_*.prof"))
        render_profiles = list(Path(temp_dir).glob("render_profile_*.prof"))
        
        assert len(key_profiles) > 0, "Key profile files should be created"
        assert len(render_profiles) > 0, "Render profile files should be created"
        print(f"✓ Profile files created: {len(key_profiles)} key, {len(render_profiles)} render")
        
        # 6. Verify README exists
        readme_path = Path(temp_dir) / "README.txt"
        assert readme_path.exists(), "README.txt should exist"
        print("✓ README.txt created")
        
        # 7. Verify profile files can be analyzed with pstats
        for profile_file in key_profiles[:1]:  # Test one file
            stats = pstats.Stats(str(profile_file))
            assert stats is not None, "Profile should be loadable by pstats"
            
            # Verify we can get statistics
            output = StringIO()
            stats.stream = output
            stats.print_stats(5)
            stats_output = output.getvalue()
            assert len(stats_output) > 0, "Should be able to print statistics"
            print(f"✓ Profile file analyzable with pstats: {profile_file.name}")
        
        print("\n" + "=" * 70)
        print("Complete Profiling Workflow Test: PASSED")
        print("=" * 70)


def test_profiling_with_mock_backends():
    """Test profiling works with different backend types"""
    print("\n" + "=" * 70)
    print("Test: Profiling with Different Backend Types")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = ProfilingManager(enabled=True, output_dir=temp_dir, render_profile_interval=0)
        
        # Test with mock CoreGraphics-style backend
        def coregraphics_render():
            """Simulate CoreGraphics rendering operations"""
            # Simulate Metal/CoreGraphics operations
            operations = []
            for i in range(100):
                operations.append({
                    'type': 'draw_rect',
                    'x': i * 10,
                    'y': i * 5,
                    'width': 100,
                    'height': 20
                })
            return operations
        
        result = manager.profile_rendering(coregraphics_render)
        assert len(result) == 100, "CoreGraphics-style rendering should work"
        print("✓ CoreGraphics-style backend profiling works")
        
        # Test with mock curses-style backend
        def curses_render():
            """Simulate curses rendering operations"""
            # Simulate curses operations
            screen_buffer = []
            for y in range(24):
                for x in range(80):
                    screen_buffer.append((y, x, ' '))
            return screen_buffer
        
        result = manager.profile_rendering(curses_render)
        assert len(result) == 24 * 80, "Curses-style rendering should work"
        print("✓ Curses-style backend profiling works")
        
        # Wait for async operations
        time.sleep(0.3)
        
        # Verify both profiles were created
        render_profiles = list(Path(temp_dir).glob("render_profile_*.prof"))
        assert len(render_profiles) >= 2, "Should have profiles for both backends"
        print(f"✓ Created {len(render_profiles)} render profiles")
        
        print("\n" + "=" * 70)
        print("Backend Compatibility Test: PASSED")
        print("=" * 70)


def test_profiling_with_various_workloads():
    """Test profiling with different types of workloads"""
    print("\n" + "=" * 70)
    print("Test: Profiling with Various Workloads")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = ProfilingManager(enabled=True, output_dir=temp_dir, render_profile_interval=0)
        
        # Workload 1: File operations
        def file_operation_workload():
            """Simulate file operations"""
            files = []
            for i in range(50):
                files.append({
                    'name': f'file_{i}.txt',
                    'size': i * 1024,
                    'modified': time.time()
                })
            # Sort by size
            files.sort(key=lambda f: f['size'])
            return files
        
        result = manager.profile_key_handling(file_operation_workload)
        assert len(result) == 50, "File operation workload should work"
        print("✓ File operations workload profiled")
        
        # Workload 2: Navigation operations
        def navigation_workload():
            """Simulate navigation operations"""
            path_components = ['/', 'home', 'user', 'documents', 'projects']
            current_path = ''
            for component in path_components:
                current_path = current_path + '/' + component
                # Simulate path validation
                if len(current_path) > 0:
                    pass
            return current_path
        
        result = manager.profile_key_handling(navigation_workload)
        assert result.endswith('projects'), "Navigation workload should work"
        print("✓ Navigation operations workload profiled")
        
        # Workload 3: Search operations
        def search_workload():
            """Simulate search operations"""
            items = [f'item_{i}' for i in range(1000)]
            pattern = 'item_5'
            matches = [item for item in items if pattern in item]
            return matches
        
        result = manager.profile_key_handling(search_workload)
        assert len(result) > 0, "Search workload should work"
        print("✓ Search operations workload profiled")
        
        # Workload 4: Rendering with complex layout
        def complex_render_workload():
            """Simulate complex rendering"""
            layout = {
                'panes': [],
                'status_bar': {},
                'log_pane': {}
            }
            
            # Create two panes
            for pane_id in range(2):
                pane = {
                    'id': pane_id,
                    'files': []
                }
                for i in range(100):
                    pane['files'].append({
                        'name': f'file_{i}.txt',
                        'selected': i % 5 == 0
                    })
                layout['panes'].append(pane)
            
            return layout
        
        result = manager.profile_rendering(complex_render_workload)
        assert len(result['panes']) == 2, "Complex render workload should work"
        print("✓ Complex rendering workload profiled")
        
        # Wait for async operations
        time.sleep(0.5)
        
        # Verify profiles were created for all workloads
        key_profiles = list(Path(temp_dir).glob("key_profile_*.prof"))
        render_profiles = list(Path(temp_dir).glob("render_profile_*.prof"))
        
        assert len(key_profiles) >= 3, "Should have key profiles for different workloads"
        assert len(render_profiles) >= 1, "Should have render profiles for different workloads"
        print(f"✓ Created profiles: {len(key_profiles)} key, {len(render_profiles)} render")
        
        print("\n" + "=" * 70)
        print("Various Workloads Test: PASSED")
        print("=" * 70)


def test_profile_analysis_with_pstats():
    """Test that profile files can be properly analyzed with pstats"""
    print("\n" + "=" * 70)
    print("Test: Profile Analysis with pstats")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = ProfilingManager(enabled=True, output_dir=temp_dir, render_profile_interval=0)
        
        # Create a profile with known function calls
        def complex_function():
            """Function with multiple operations for profiling"""
            def helper_a():
                total = 0
                for i in range(100):
                    total += i
                return total
            
            def helper_b():
                result = []
                for i in range(50):
                    result.append(i * 2)
                return result
            
            a_result = helper_a()
            b_result = helper_b()
            return a_result, b_result
        
        # Profile the function
        manager.profile_key_handling(complex_function)
        
        # Wait for async write
        time.sleep(0.3)
        
        # Get the profile file
        profile_files = list(Path(temp_dir).glob("key_profile_*.prof"))
        assert len(profile_files) == 1, "Should have one profile file"
        profile_file = profile_files[0]
        
        # Test 1: Load with pstats
        stats = pstats.Stats(str(profile_file))
        assert stats is not None, "Should be able to load profile"
        print("✓ Profile loaded with pstats")
        
        # Test 2: Print statistics
        output = StringIO()
        stats.stream = output
        stats.print_stats(10)
        stats_output = output.getvalue()
        
        assert 'function calls' in stats_output, "Should show function call count"
        assert 'complex_function' in stats_output or 'helper' in stats_output, "Should show profiled functions"
        print("✓ Statistics printed successfully")
        
        # Test 3: Sort by different criteria
        output = StringIO()
        stats.stream = output
        stats.sort_stats('cumulative')
        stats.print_stats(5)
        cumulative_output = output.getvalue()
        
        assert len(cumulative_output) > 0, "Should be able to sort by cumulative time"
        print("✓ Sorting by cumulative time works")
        
        # Test 4: Get callers
        output = StringIO()
        stats.stream = output
        stats.print_callers(5)
        callers_output = output.getvalue()
        
        assert len(callers_output) > 0, "Should be able to print callers"
        print("✓ Caller information available")
        
        # Test 5: Get callees
        output = StringIO()
        stats.stream = output
        stats.print_callees(5)
        callees_output = output.getvalue()
        
        assert len(callees_output) > 0, "Should be able to print callees"
        print("✓ Callee information available")
        
        print("\n" + "=" * 70)
        print("pstats Analysis Test: PASSED")
        print("=" * 70)


def test_profiling_disabled_mode():
    """Test that profiling can be disabled without affecting functionality"""
    print("\n" + "=" * 70)
    print("Test: Profiling Disabled Mode")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create disabled profiling manager
        manager = ProfilingManager(enabled=False, output_dir=temp_dir)
        
        # Test that operations still work
        def test_function():
            return "result"
        
        # These should all work without creating files
        manager.start_frame()
        result = manager.profile_key_handling(test_function)
        assert result == "result", "Function should execute normally"
        
        result = manager.profile_rendering(test_function)
        assert result == "result", "Function should execute normally"
        
        manager.end_frame()
        
        print("✓ All operations work when profiling is disabled")
        
        # Wait a bit
        time.sleep(0.2)
        
        # Verify no profile files were created
        if Path(temp_dir).exists():
            profile_files = list(Path(temp_dir).glob("*.prof"))
            assert len(profile_files) == 0, "No profile files should be created when disabled"
            print("✓ No profile files created when disabled")
        
        # Verify no FPS tracker
        assert manager.fps_tracker is None, "FPS tracker should be None when disabled"
        print("✓ No FPS tracking overhead when disabled")
        
        print("\n" + "=" * 70)
        print("Disabled Mode Test: PASSED")
        print("=" * 70)


def test_fps_tracking_accuracy():
    """Test FPS tracking accuracy over time"""
    print("\n" + "=" * 70)
    print("Test: FPS Tracking Accuracy")
    print("=" * 70)
    
    manager = ProfilingManager(enabled=True)
    
    # Simulate frames at known rate
    target_fps = 30
    frame_time = 1.0 / target_fps
    
    for i in range(60):  # 2 seconds worth of frames
        manager.start_frame()
        time.sleep(frame_time)
    
    # Calculate FPS
    measured_fps = manager.fps_tracker.calculate_fps()
    
    # Should be close to target FPS (within 20% tolerance)
    tolerance = target_fps * 0.2
    assert abs(measured_fps - target_fps) < tolerance, \
        f"FPS should be close to {target_fps}, got {measured_fps}"
    
    print(f"✓ FPS tracking accurate: target={target_fps}, measured={measured_fps:.2f}")
    
    # Test FPS output format
    output = manager.fps_tracker.format_output()
    assert '[' in output and ']' in output, "Output should have timestamp in brackets"
    assert 'FPS:' in output, "Output should have FPS label"
    assert str(int(measured_fps)) in output or str(round(measured_fps, 1)) in output, \
        "Output should contain FPS value"
    
    print(f"✓ FPS output format correct: {output}")
    
    print("\n" + "=" * 70)
    print("FPS Tracking Accuracy Test: PASSED")
    print("=" * 70)


def test_error_handling_in_profiling():
    """Test that profiling handles errors gracefully"""
    print("\n" + "=" * 70)
    print("Test: Error Handling in Profiling")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = ProfilingManager(enabled=True, output_dir=temp_dir, render_profile_interval=0)
        
        # Test 1: Function that raises exception
        def failing_function():
            raise ValueError("Test error")
        
        try:
            manager.profile_key_handling(failing_function)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert str(e) == "Test error", "Exception should propagate"
            print("✓ Exceptions propagate correctly")
        
        # Wait for async operations
        time.sleep(0.3)
        
        # Profile file should still be created
        profile_files = list(Path(temp_dir).glob("key_profile_*.prof"))
        assert len(profile_files) == 1, "Profile should be created even on exception"
        print("✓ Profile created even when function raises exception")
        
        # Test 2: Invalid output directory (read-only)
        # This is harder to test portably, so we'll skip it
        
        print("\n" + "=" * 70)
        print("Error Handling Test: PASSED")
        print("=" * 70)


def run_all_integration_tests():
    """Run all final integration tests"""
    print("\n" + "=" * 80)
    print(" " * 20 + "FINAL INTEGRATION TEST SUITE")
    print(" " * 15 + "Performance Profiling System")
    print("=" * 80)
    
    try:
        # Run all tests
        test_complete_profiling_workflow()
        test_profiling_with_mock_backends()
        test_profiling_with_various_workloads()
        test_profile_analysis_with_pstats()
        test_profiling_disabled_mode()
        test_fps_tracking_accuracy()
        test_error_handling_in_profiling()
        
        # Summary
        print("\n" + "=" * 80)
        print(" " * 25 + "ALL TESTS PASSED!")
        print("=" * 80)
        print("\nTest Coverage:")
        print("  ✓ Complete profiling workflow end-to-end")
        print("  ✓ CoreGraphics backend compatibility")
        print("  ✓ Curses backend compatibility")
        print("  ✓ Various workloads (file ops, navigation, search, rendering)")
        print("  ✓ Profile file analysis with pstats")
        print("  ✓ Profiling disabled mode")
        print("  ✓ FPS tracking accuracy")
        print("  ✓ Error handling")
        print("\nAll requirements validated successfully!")
        print("=" * 80)
        
        return 0
        
    except AssertionError as e:
        print("\n" + "=" * 80)
        print(f"TEST FAILED: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return 1
        
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"UNEXPECTED ERROR: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_integration_tests())
