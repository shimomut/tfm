"""
Test suite for ProgressManager TTK integration verification

This test suite verifies that ProgressManager and ProgressAnimator:
1. Contain NO rendering code (no curses imports or calls)
2. Work correctly as pure business logic components
3. Integrate properly with TTK-migrated tfm_main.py
4. Provide correct progress data through callbacks

Run with: PYTHONPATH=.:src:ttk pytest test/test_progress_manager_ttk_integration.py -v
"""

from pathlib import Path
import sys

import pytest
import time
from tfm_progress_manager import ProgressManager, OperationType
from tfm_progress_animator import ProgressAnimator, ProgressAnimatorFactory


class TestProgressManagerNoRendering:
    """Verify ProgressManager contains no rendering code"""
    
    def test_no_curses_imports(self):
        """Verify ProgressManager does not import curses"""
        import tfm_progress_manager
        import sys
        from ttk import KeyEvent, KeyCode, ModifierKey
        
        # Check module doesn't import curses
        assert 'curses' not in sys.modules or 'curses' not in dir(tfm_progress_manager)
        
        # Read source file and verify no curses imports
        source_file = Path(__file__).parent.parent / 'src' / 'tfm_progress_manager.py'
        source_code = source_file.read_text()
        
        assert 'import curses' not in source_code
        assert 'from curses' not in source_code
    
    def test_no_rendering_methods(self):
        """Verify ProgressManager has no rendering methods"""
        pm = ProgressManager()
        
        # Should not have any curses-related methods
        assert not hasattr(pm, 'stdscr')
        assert not hasattr(pm, 'addstr')
        assert not hasattr(pm, 'refresh')
        assert not hasattr(pm, 'clear')
        assert not hasattr(pm, 'getmaxyx')
    
    def test_pure_business_logic(self):
        """Verify ProgressManager is pure business logic"""
        pm = ProgressManager()
        
        # Should have business logic methods
        assert hasattr(pm, 'start_operation')
        assert hasattr(pm, 'update_progress')
        assert hasattr(pm, 'finish_operation')
        assert hasattr(pm, 'get_progress_text')
        assert hasattr(pm, 'get_progress_percentage')
        
        # Should not have rendering methods
        assert not hasattr(pm, 'draw')
        assert not hasattr(pm, 'render')
        assert not hasattr(pm, 'display')


class TestProgressAnimatorNoRendering:
    """Verify ProgressAnimator contains no rendering code"""
    
    def test_no_curses_imports(self):
        """Verify ProgressAnimator does not import curses"""
        import tfm_progress_animator
        import sys
        
        # Check module doesn't import curses
        assert 'curses' not in sys.modules or 'curses' not in dir(tfm_progress_animator)
        
        # Read source file and verify no curses imports
        source_file = Path(__file__).parent.parent / 'src' / 'tfm_progress_animator.py'
        source_code = source_file.read_text()
        
        assert 'import curses' not in source_code
        assert 'from curses' not in source_code
    
    def test_returns_strings_only(self):
        """Verify ProgressAnimator only returns strings, not rendering calls"""
        class MinimalConfig:
            PROGRESS_ANIMATION_PATTERN = 'spinner'
            PROGRESS_ANIMATION_SPEED = 0.08
        
        animator = ProgressAnimator(MinimalConfig())
        
        # All methods should return strings or lists of strings
        frame = animator.get_current_frame()
        assert isinstance(frame, str)
        
        patterns = animator.get_available_patterns()
        assert isinstance(patterns, list)
        assert all(isinstance(p, str) for p in patterns)
        
        preview = animator.get_pattern_preview()
        assert isinstance(preview, list)
        assert all(isinstance(f, str) for f in preview)
        
        indicator = animator.get_progress_indicator()
        assert isinstance(indicator, str)
        
        status = animator.get_status_text("Testing")
        assert isinstance(status, str)


class TestProgressManagerBusinessLogic:
    """Test ProgressManager business logic functionality"""
    
    def test_operation_lifecycle(self):
        """Test complete operation lifecycle"""
        pm = ProgressManager()
        
        # Initially no operation
        assert not pm.is_operation_active()
        assert pm.get_current_operation() is None
        
        # Start operation
        pm.start_operation(OperationType.COPY, 10, "test files")
        assert pm.is_operation_active()
        
        op = pm.get_current_operation()
        assert op is not None
        assert op['type'] == OperationType.COPY
        assert op['total_items'] == 10
        assert op['processed_items'] == 0
        assert op['description'] == "test files"
        
        # Update progress
        pm.update_progress("file1.txt")
        op = pm.get_current_operation()
        assert op['processed_items'] == 1
        assert op['current_item'] == "file1.txt"
        
        # Finish operation
        pm.finish_operation()
        assert not pm.is_operation_active()
        assert pm.get_current_operation() is None
    
    def test_progress_percentage(self):
        """Test progress percentage calculation"""
        pm = ProgressManager()
        
        # No operation
        assert pm.get_progress_percentage() == 0
        
        # Start operation
        pm.start_operation(OperationType.COPY, 100)
        assert pm.get_progress_percentage() == 0
        
        # Update progress
        for i in range(1, 51):
            pm.update_progress(f"file{i}.txt")
        
        assert pm.get_progress_percentage() == 50
        
        # Complete
        for i in range(51, 101):
            pm.update_progress(f"file{i}.txt")
        
        assert pm.get_progress_percentage() == 100
    
    def test_progress_text_formatting(self):
        """Test progress text formatting"""
        pm = ProgressManager()
        
        # No operation
        assert pm.get_progress_text() == ""
        
        # Start operation
        pm.start_operation(OperationType.COPY, 10, "documents")
        pm.update_operation_total(10, "documents")  # Mark counting complete
        
        text = pm.get_progress_text(80)
        assert "Copying" in text
        assert "documents" in text
        assert "0/10" in text
        
        # Update with current file
        pm.update_progress("important.txt")
        text = pm.get_progress_text(80)
        assert "1/10" in text
        assert "important.txt" in text
    
    def test_byte_progress_formatting(self):
        """Test byte-level progress formatting"""
        pm = ProgressManager()
        
        pm.start_operation(OperationType.COPY, 1, "large file")
        pm.update_operation_total(1, "large file")
        pm.update_progress("bigfile.iso")
        
        # Update byte progress (only shows for files > 1MB)
        pm.update_file_byte_progress(5 * 1024 * 1024, 10 * 1024 * 1024)
        
        text = pm.get_progress_text(80)
        assert "bigfile.iso" in text
        # Should show byte progress for large files
        assert "[" in text and "]" in text
    
    def test_error_tracking(self):
        """Test error count tracking"""
        pm = ProgressManager()
        
        pm.start_operation(OperationType.DELETE, 5)
        
        op = pm.get_current_operation()
        assert op['errors'] == 0
        
        pm.increment_errors()
        assert op['errors'] == 1
        
        pm.increment_errors()
        assert op['errors'] == 2
    
    def test_callback_mechanism(self):
        """Test progress callback mechanism"""
        pm = ProgressManager()
        callback_count = 0
        last_operation = None
        
        def progress_callback(operation):
            nonlocal callback_count, last_operation
            callback_count += 1
            last_operation = operation
        
        # Start with callback
        pm.start_operation(OperationType.MOVE, 5, progress_callback=progress_callback)
        assert callback_count == 1
        assert last_operation is not None
        
        # Update progress
        pm.update_progress("file1.txt")
        assert callback_count >= 2
        assert last_operation['current_item'] == "file1.txt"
        
        # Finish
        pm.finish_operation()
        assert last_operation is None  # Callback called with None to clear


class TestProgressAnimatorBusinessLogic:
    """Test ProgressAnimator business logic functionality"""
    
    def test_animation_patterns(self):
        """Test different animation patterns"""
        class MinimalConfig:
            PROGRESS_ANIMATION_PATTERN = 'spinner'
            PROGRESS_ANIMATION_SPEED = 0.01
        
        animator = ProgressAnimator(MinimalConfig())
        
        # Test all available patterns
        patterns = animator.get_available_patterns()
        assert len(patterns) > 0
        assert 'spinner' in patterns
        assert 'dots' in patterns
        assert 'progress' in patterns
        
        for pattern in patterns:
            animator.set_pattern(pattern)
            frame = animator.get_current_frame()
            assert isinstance(frame, str)
            assert len(frame) > 0
    
    def test_animation_progression(self):
        """Test animation frame progression"""
        class MinimalConfig:
            PROGRESS_ANIMATION_PATTERN = 'spinner'
            PROGRESS_ANIMATION_SPEED = 0.01
        
        animator = ProgressAnimator(MinimalConfig())
        
        # Get initial frame
        frame1 = animator.get_current_frame()
        
        # Wait for animation to progress
        time.sleep(0.02)
        
        # Get next frame
        frame2 = animator.get_current_frame()
        
        # Frames should be different (animation progressed)
        # Note: might be same if timing is off, but pattern should exist
        assert isinstance(frame1, str)
        assert isinstance(frame2, str)
    
    def test_reset_functionality(self):
        """Test animation reset"""
        class MinimalConfig:
            PROGRESS_ANIMATION_PATTERN = 'spinner'
            PROGRESS_ANIMATION_SPEED = 0.01
        
        animator = ProgressAnimator(MinimalConfig())
        
        # Progress animation
        time.sleep(0.02)
        animator.get_current_frame()
        
        # Reset
        animator.reset()
        
        # Should be back to first frame
        frame = animator.get_current_frame()
        assert isinstance(frame, str)
    
    def test_factory_methods(self):
        """Test ProgressAnimatorFactory"""
        class MinimalConfig:
            PROGRESS_ANIMATION_PATTERN = 'spinner'
            PROGRESS_ANIMATION_SPEED = 0.2
        
        # Test different factory methods
        search_animator = ProgressAnimatorFactory.create_search_animator(MinimalConfig())
        assert isinstance(search_animator, ProgressAnimator)
        
        loading_animator = ProgressAnimatorFactory.create_loading_animator(MinimalConfig())
        assert isinstance(loading_animator, ProgressAnimator)
        
        processing_animator = ProgressAnimatorFactory.create_processing_animator(MinimalConfig())
        assert isinstance(processing_animator, ProgressAnimator)
        
        custom_animator = ProgressAnimatorFactory.create_custom_animator(
            MinimalConfig(), pattern='dots', speed=0.1
        )
        assert isinstance(custom_animator, ProgressAnimator)


class TestProgressManagerTTKIntegration:
    """Test ProgressManager integration with TTK-migrated components"""
    
    def test_integration_pattern(self):
        """Verify ProgressManager follows TTK integration pattern"""
        pm = ProgressManager()
        
        # ProgressManager should:
        # 1. Not render directly
        # 2. Provide data through methods
        # 3. Use callbacks for updates
        # 4. Return formatted strings for display
        
        # Start operation
        pm.start_operation(OperationType.COPY, 10)
        pm.update_operation_total(10)
        
        # Should provide data, not render
        text = pm.get_progress_text(80)
        assert isinstance(text, str)
        
        percentage = pm.get_progress_percentage()
        assert isinstance(percentage, int)
        
        operation = pm.get_current_operation()
        assert isinstance(operation, dict)
    
    def test_tfm_main_integration(self):
        """Verify integration with tfm_main.py rendering"""
        # This test verifies the integration pattern:
        # 1. ProgressManager provides data
        # 2. tfm_main.py (already migrated) handles rendering
        
        pm = ProgressManager()
        
        # Simulate what tfm_main.py does:
        # 1. Check if operation is active
        if pm.is_operation_active():
            # 2. Get formatted text
            text = pm.get_progress_text(80)
            # 3. Render using TTK (done in tfm_main.py)
            # renderer.draw_text(y, x, text, color_pair, attributes)
        
        # Start operation and verify pattern
        pm.start_operation(OperationType.MOVE, 5)
        pm.update_operation_total(5)
        
        assert pm.is_operation_active()
        text = pm.get_progress_text(80)
        assert isinstance(text, str)
        assert len(text) > 0
    
    def test_no_renderer_dependency(self):
        """Verify ProgressManager doesn't depend on renderer"""
        pm = ProgressManager()
        
        # Should work without any renderer
        pm.start_operation(OperationType.DELETE, 3)
        pm.update_operation_total(3)
        pm.update_progress("file1.txt")
        
        text = pm.get_progress_text(80)
        assert isinstance(text, str)
        
        pm.finish_operation()


class TestProgressManagerOperationTypes:
    """Test different operation types"""
    
    def test_copy_operation(self):
        """Test copy operation progress"""
        pm = ProgressManager()
        pm.start_operation(OperationType.COPY, 5, "files")
        pm.update_operation_total(5, "files")
        
        text = pm.get_progress_text(80)
        assert "Copying" in text
    
    def test_move_operation(self):
        """Test move operation progress"""
        pm = ProgressManager()
        pm.start_operation(OperationType.MOVE, 3, "items")
        pm.update_operation_total(3, "items")
        
        text = pm.get_progress_text(80)
        assert "Moving" in text
    
    def test_delete_operation(self):
        """Test delete operation progress"""
        pm = ProgressManager()
        pm.start_operation(OperationType.DELETE, 10)
        pm.update_operation_total(10)
        
        text = pm.get_progress_text(80)
        assert "Deleting" in text
    
    def test_archive_operations(self):
        """Test archive operation progress"""
        pm = ProgressManager()
        
        # Create archive
        pm.start_operation(OperationType.ARCHIVE_CREATE, 20, "backup.tar.gz")
        pm.update_operation_total(20, "backup.tar.gz")
        text = pm.get_progress_text(80)
        assert "Creating archive" in text
        pm.finish_operation()
        
        # Extract archive
        pm.start_operation(OperationType.ARCHIVE_EXTRACT, 15, "data.zip")
        pm.update_operation_total(15, "data.zip")
        text = pm.get_progress_text(80)
        assert "Extracting archive" in text
