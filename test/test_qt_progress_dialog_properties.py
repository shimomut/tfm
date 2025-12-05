"""
Property-Based Tests for Qt Progress Dialog

This module contains property-based tests for the Qt progress dialog,
validating the correctness properties defined in the design document.

**Feature: qt-gui-port, Property 17: Progress bar updates**
**Feature: qt-gui-port, Property 18: Current file display in progress**
**Feature: qt-gui-port, Property 19: Progress dialog auto-close**
**Feature: qt-gui-port, Property 20: Operation cancellation**
"""

import sys
import unittest
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Qt imports
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtTest import QTest
    
    from tfm_qt_progress_dialog import ProgressDialog
    
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    print("Warning: PySide6 not available, skipping Qt progress dialog property tests")


@unittest.skipIf(not QT_AVAILABLE, "PySide6 not available")
class TestProgressDialogProperties(unittest.TestCase):
    """Property-based tests for progress dialog behavior"""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests"""
        if QT_AVAILABLE:
            cls.app = QApplication.instance()
            if cls.app is None:
                cls.app = QApplication(sys.argv)
    
    def setUp(self):
        """Set up test fixtures"""
        self.dialog = None
    
    def tearDown(self):
        """Clean up after each test"""
        if self.dialog:
            self.dialog.close()
            self.dialog = None
        
        # Process events to ensure cleanup
        if QT_AVAILABLE:
            QApplication.processEvents()
    
    @given(
        current=st.integers(min_value=0, max_value=1000),
        total=st.integers(min_value=1, max_value=1000),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_17_progress_bar_updates(self, current, total):
        """
        **Feature: qt-gui-port, Property 17: Progress bar updates**
        
        For any file copy operation, the progress bar should update to reflect 
        the current completion percentage as files are copied.
        
        **Validates: Requirements 7.2**
        """
        # Ensure current doesn't exceed total
        assume(current <= total)
        
        # Create progress dialog
        self.dialog = ProgressDialog(
            parent=None,
            title="Test Progress",
            operation="Testing",
            cancelable=True
        )
        
        # Update progress
        self.dialog.update_progress(current, total, "")
        
        # Process events to update UI
        QApplication.processEvents()
        
        # Calculate expected percentage
        expected_percentage = int((current / total) * 100)
        
        # Verify progress bar value matches expected percentage
        actual_percentage = self.dialog.progress_bar.value()
        
        assert actual_percentage == expected_percentage, \
            f"Progress bar should show {expected_percentage}% but shows {actual_percentage}%"
        
        # Verify progress bar format string contains the values
        format_str = self.dialog.progress_bar.format()
        assert str(current) in format_str, \
            f"Progress format should contain current value {current}"
        assert str(total) in format_str, \
            f"Progress format should contain total value {total}"
        assert str(expected_percentage) in format_str, \
            f"Progress format should contain percentage {expected_percentage}"
    
    @given(
        current=st.integers(min_value=0, max_value=100),
        total=st.integers(min_value=1, max_value=100),
        message=st.text(min_size=1, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Zs'),
            blacklist_characters='\x00\n\r\t'
        ))
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_18_current_file_display(self, current, total, message):
        """
        **Feature: qt-gui-port, Property 18: Current file display in progress**
        
        For any multi-file operation, the progress dialog should show the name 
        of the file currently being processed.
        
        **Validates: Requirements 7.3**
        """
        # Ensure current doesn't exceed total
        assume(current <= total)
        
        # Create progress dialog
        self.dialog = ProgressDialog(
            parent=None,
            title="Test Progress",
            operation="Processing files",
            cancelable=True
        )
        
        # Update progress with message (current file name)
        self.dialog.update_progress(current, total, message)
        
        # Process events to update UI
        QApplication.processEvents()
        
        # Verify message label contains the current file name
        displayed_message = self.dialog.message_label.text()
        
        assert displayed_message == message, \
            f"Message label should display '{message}' but shows '{displayed_message}'"
    
    @given(
        total=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_19_progress_dialog_auto_close(self, total):
        """
        **Feature: qt-gui-port, Property 19: Progress dialog auto-close**
        
        For any long-running operation, when it completes successfully, 
        the progress dialog should close automatically.
        
        **Validates: Requirements 7.4**
        """
        # Create progress dialog
        self.dialog = ProgressDialog(
            parent=None,
            title="Test Progress",
            operation="Testing auto-close",
            cancelable=True
        )
        
        # Show the dialog
        self.dialog.show()
        QApplication.processEvents()
        
        # Verify dialog is visible
        assert self.dialog.isVisible(), "Dialog should be visible initially"
        
        # Update progress to completion (current == total)
        self.dialog.update_progress(total, total, "Complete")
        QApplication.processEvents()
        
        # Call auto_close (this is what the backend does when operation completes)
        self.dialog.auto_close()
        QApplication.processEvents()
        
        # Verify dialog is no longer visible (closed)
        assert not self.dialog.isVisible(), \
            "Dialog should be closed after auto_close() is called"
    
    @given(
        current=st.integers(min_value=0, max_value=50),
        total=st.integers(min_value=51, max_value=100),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_20_operation_cancellation(self, current, total):
        """
        **Feature: qt-gui-port, Property 20: Operation cancellation**
        
        For any cancellable operation, clicking Cancel in the progress dialog 
        should abort the operation and stop further processing.
        
        **Validates: Requirements 7.5**
        """
        # Ensure we're not at completion
        assume(current < total)
        
        # Create cancelable progress dialog
        self.dialog = ProgressDialog(
            parent=None,
            title="Test Progress",
            operation="Testing cancellation",
            cancelable=True
        )
        
        # Show the dialog
        self.dialog.show()
        QApplication.processEvents()
        
        # Update progress to some intermediate value
        self.dialog.update_progress(current, total, "Processing...")
        QApplication.processEvents()
        
        # Verify dialog is not cancelled initially
        assert not self.dialog.was_cancelled(), \
            "Dialog should not be cancelled initially"
        
        # Track if cancelled signal was emitted
        cancelled_signal_received = [False]
        
        def on_cancelled():
            cancelled_signal_received[0] = True
        
        self.dialog.cancelled.connect(on_cancelled)
        
        # Simulate clicking the cancel button
        if hasattr(self.dialog, 'cancel_button'):
            # Trigger the cancel button click
            self.dialog.cancel_button.click()
            QApplication.processEvents()
            
            # Verify cancellation state
            assert self.dialog.was_cancelled(), \
                "Dialog should be marked as cancelled after cancel button click"
            
            # Verify cancelled signal was emitted
            assert cancelled_signal_received[0], \
                "Cancelled signal should be emitted when cancel button is clicked"
            
            # Verify cancel button is disabled after clicking
            assert not self.dialog.cancel_button.isEnabled(), \
                "Cancel button should be disabled after clicking to prevent multiple cancellations"
            
            # Verify cancel button text changed
            assert "Cancelling" in self.dialog.cancel_button.text(), \
                "Cancel button text should indicate cancellation in progress"
    
    @given(
        updates=st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=100),
                st.integers(min_value=1, max_value=100),
                st.text(min_size=1, max_size=50, alphabet=st.characters(
                    whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
                    blacklist_characters='\x00\n\r\t'
                ))
            ),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_progress_updates_are_monotonic(self, updates):
        """
        Additional property: Progress updates should handle multiple sequential updates correctly.
        
        This ensures that the progress dialog can handle a sequence of updates
        without errors or inconsistent state.
        """
        # Create progress dialog
        self.dialog = ProgressDialog(
            parent=None,
            title="Test Progress",
            operation="Testing sequential updates",
            cancelable=True
        )
        
        # Track the last non-empty message
        last_message = ""
        
        # Apply all updates
        for current, total, message in updates:
            # Ensure current doesn't exceed total
            if current > total:
                current = total
            
            # Update progress
            self.dialog.update_progress(current, total, message)
            QApplication.processEvents()
            
            # Verify progress bar value is within valid range
            actual_percentage = self.dialog.progress_bar.value()
            assert 0 <= actual_percentage <= 100, \
                f"Progress percentage should be between 0 and 100, got {actual_percentage}"
            
            # Track last non-empty message (implementation only updates if message is non-empty)
            if message:
                last_message = message
            
            # Verify message is displayed (should be the last non-empty message)
            displayed_message = self.dialog.message_label.text()
            assert displayed_message == last_message, \
                f"Message should be '{last_message}' but is '{displayed_message}'"
    
    def test_non_cancelable_dialog_has_no_cancel_button(self):
        """
        Test that non-cancelable dialogs don't have a cancel button.
        
        This ensures that operations that cannot be cancelled don't mislead
        users by showing a cancel button.
        """
        # Create non-cancelable progress dialog
        self.dialog = ProgressDialog(
            parent=None,
            title="Test Progress",
            operation="Non-cancelable operation",
            cancelable=False
        )
        
        # Verify no cancel button exists
        assert not hasattr(self.dialog, 'cancel_button'), \
            "Non-cancelable dialog should not have a cancel button"
        
        # Verify dialog cannot be cancelled
        assert not self.dialog.was_cancelled(), \
            "Non-cancelable dialog should never be in cancelled state"
    
    def test_indeterminate_progress(self):
        """
        Test that progress dialog handles indeterminate progress (total=0).
        
        This is useful for operations where the total amount of work is unknown.
        """
        # Create progress dialog
        self.dialog = ProgressDialog(
            parent=None,
            title="Test Progress",
            operation="Indeterminate operation",
            cancelable=True
        )
        
        # Update with total=0 for indeterminate progress
        self.dialog.update_progress(0, 0, "Processing...")
        QApplication.processEvents()
        
        # Verify progress bar is in indeterminate mode
        assert self.dialog.progress_bar.maximum() == 0, \
            "Progress bar should be in indeterminate mode (maximum=0)"


if __name__ == '__main__':
    unittest.main()
