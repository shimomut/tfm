"""
Unit tests for drag-and-drop error handling.

This module tests error scenarios and user feedback for drag-and-drop operations,
including error messages for remote files, archive contents, missing files, and
too many files.

Run with: PYTHONPATH=.:src:ttk pytest test/test_drag_error_handling.py -v
"""

from pathlib import Path
import pytest
from unittest.mock import Mock, MagicMock, patch

from tfm_drag_payload import DragPayloadBuilder
from tfm_drag_session import DragSessionManager, DragState


class TestDragPayloadErrorMessages:
    """Test error message generation in DragPayloadBuilder."""
    
    def test_error_message_for_remote_files(self, tmp_path):
        """Test that remote files generate appropriate error message."""
        builder = DragPayloadBuilder()
        
        # Create a mock S3 path (using tfm_path.Path which handles S3)
        from tfm_path import Path as TFMPath
        remote_file = TFMPath("s3://bucket/file.txt")
        
        # Attempt to build payload
        urls = builder.build_payload(
            selected_files=[remote_file],
            focused_item=None,
            current_directory=tmp_path
        )
        
        # Verify payload is None
        assert urls is None
        
        # Verify error message is set
        error = builder.get_last_error()
        assert error is not None
        assert "remote files" in error.lower()
        assert "S3" in error or "SSH" in error
    
    def test_error_message_for_archive_contents(self, tmp_path):
        """Test that archive contents generate appropriate error message."""
        builder = DragPayloadBuilder()
        
        # Create a mock archive content path
        archive_file = tmp_path / "archive.zip::archive::file.txt"
        
        # Attempt to build payload
        urls = builder.build_payload(
            selected_files=[archive_file],
            focused_item=None,
            current_directory=tmp_path
        )
        
        # Verify payload is None
        assert urls is None
        
        # Verify error message is set
        error = builder.get_last_error()
        assert error is not None
        assert "archive" in error.lower()
        assert "extract" in error.lower()
    
    def test_error_message_for_missing_files(self, tmp_path):
        """Test that missing files generate appropriate error message."""
        builder = DragPayloadBuilder()
        
        # Create a path to a non-existent file
        missing_file = tmp_path / "nonexistent.txt"
        
        # Attempt to build payload
        urls = builder.build_payload(
            selected_files=[missing_file],
            focused_item=None,
            current_directory=tmp_path
        )
        
        # Verify payload is None
        assert urls is None
        
        # Verify error message is set
        error = builder.get_last_error()
        assert error is not None
        assert "exist" in error.lower()
        assert "nonexistent.txt" in error
    
    def test_error_message_for_too_many_files(self, tmp_path):
        """Test that too many files generate appropriate error message."""
        builder = DragPayloadBuilder()
        
        # Create more files than the limit
        files = []
        for i in range(builder.MAX_FILES + 1):
            file_path = tmp_path / f"file_{i}.txt"
            file_path.write_text("test")
            files.append(file_path)
        
        # Attempt to build payload
        urls = builder.build_payload(
            selected_files=files,
            focused_item=None,
            current_directory=tmp_path
        )
        
        # Verify payload is None
        assert urls is None
        
        # Verify error message is set
        error = builder.get_last_error()
        assert error is not None
        assert str(builder.MAX_FILES) in error
        assert str(len(files)) in error
        assert "cannot drag more than" in error.lower()
    
    def test_no_error_message_for_parent_directory(self, tmp_path):
        """Test that parent directory marker does not generate error message."""
        builder = DragPayloadBuilder()
        
        # Create a mock parent directory marker
        parent_dir = tmp_path / ".."
        
        # Attempt to build payload
        urls = builder.build_payload(
            selected_files=[],
            focused_item=parent_dir,
            current_directory=tmp_path
        )
        
        # Verify payload is None
        assert urls is None
        
        # Verify no error message (expected behavior)
        error = builder.get_last_error()
        assert error is None
    
    def test_error_message_cleared_on_success(self, tmp_path):
        """Test that error message is cleared on successful payload build."""
        builder = DragPayloadBuilder()
        
        # First, trigger an error
        missing_file = tmp_path / "nonexistent.txt"
        urls = builder.build_payload(
            selected_files=[missing_file],
            focused_item=None,
            current_directory=tmp_path
        )
        assert urls is None
        assert builder.get_last_error() is not None
        
        # Now build a successful payload
        valid_file = tmp_path / "valid.txt"
        valid_file.write_text("test")
        urls = builder.build_payload(
            selected_files=[valid_file],
            focused_item=None,
            current_directory=tmp_path
        )
        
        # Verify success and error cleared
        assert urls is not None
        assert len(urls) == 1
        assert builder.get_last_error() is None


class TestDragSessionErrorLogging:
    """Test error logging in DragSessionManager."""
    
    def test_logs_error_when_backend_rejects_drag(self):
        """Test that OS rejection is logged as error."""
        # Create mock backend that rejects drag
        backend = Mock()
        backend.supports_drag_and_drop.return_value = True
        backend.start_drag_session.return_value = False
        
        manager = DragSessionManager(backend)
        
        # Capture log output
        with patch.object(manager.logger, 'error') as mock_error:
            success = manager.start_drag(
                urls=["file:///test.txt"],
                drag_image_text="test.txt"
            )
            
            # Verify failure
            assert not success
            assert manager.get_state() == DragState.IDLE
            
            # Verify error was logged
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0][0]
            assert "OS rejected" in call_args or "failed" in call_args.lower()
    
    def test_logs_error_when_backend_raises_exception(self):
        """Test that backend exceptions are logged."""
        # Create mock backend that raises exception
        backend = Mock()
        backend.supports_drag_and_drop.return_value = True
        backend.start_drag_session.side_effect = RuntimeError("Backend error")
        
        manager = DragSessionManager(backend)
        
        # Capture log output
        with patch.object(manager.logger, 'error') as mock_error:
            success = manager.start_drag(
                urls=["file:///test.txt"],
                drag_image_text="test.txt"
            )
            
            # Verify failure
            assert not success
            assert manager.get_state() == DragState.IDLE
            
            # Verify error was logged
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0][0]
            assert "exception" in call_args.lower()
    
    def test_logs_info_when_backend_not_supported(self):
        """Test that unsupported backend logs info, not error."""
        # Create mock backend that doesn't support drag
        backend = Mock()
        backend.supports_drag_and_drop.return_value = False
        
        manager = DragSessionManager(backend)
        
        # Capture log output
        with patch.object(manager.logger, 'info') as mock_info:
            success = manager.start_drag(
                urls=["file:///test.txt"],
                drag_image_text="test.txt"
            )
            
            # Verify failure
            assert not success
            assert manager.get_state() == DragState.IDLE
            
            # Verify info was logged (not error)
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            assert "terminal mode" in call_args.lower()
    
    def test_logs_error_in_completion_callback_exception(self):
        """Test that callback exceptions are logged but don't crash."""
        backend = Mock()
        backend.supports_drag_and_drop.return_value = True
        backend.start_drag_session.return_value = True
        
        manager = DragSessionManager(backend)
        
        # Create callback that raises exception
        def bad_callback(completed):
            raise RuntimeError("Callback error")
        
        # Start drag with bad callback
        manager.start_drag(
            urls=["file:///test.txt"],
            drag_image_text="test.txt",
            completion_callback=bad_callback
        )
        
        # Capture log output
        with patch.object(manager.logger, 'error') as mock_error:
            # Complete the drag (should catch exception)
            manager.handle_drag_completed()
            
            # Verify error was logged
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0][0]
            assert "callback" in call_args.lower()
            
            # Verify state was cleaned up despite exception
            assert manager.get_state() == DragState.IDLE
            assert manager.current_urls is None


class TestDragErrorRecovery:
    """Test error recovery and state restoration."""
    
    def test_gesture_detector_reset_on_payload_error(self):
        """Test that gesture detector is reset when payload building fails."""
        # This test would be in the FileManager integration tests
        # but we document the expected behavior here
        pass
    
    def test_gesture_detector_reset_on_session_error(self):
        """Test that gesture detector is reset when session start fails."""
        # This test would be in the FileManager integration tests
        # but we document the expected behavior here
        pass
    
    def test_state_restored_after_error(self):
        """Test that application state is restored after drag error."""
        # This test would be in the FileManager integration tests
        # but we document the expected behavior here
        pass
