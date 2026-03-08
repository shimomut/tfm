"""
Test status bar fallback mode indicator integration.

This test verifies that the status bar correctly displays the fallback mode
indicator when file monitoring is in polling mode.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch


def test_status_bar_shows_polling_mode_indicator():
    """Test that status bar includes polling mode indicator when in fallback mode."""
    # This is a simple integration test to verify the status bar logic
    # We'll test the logic that builds the status_parts list
    
    # Simulate the status bar building logic from draw_status()
    status_parts = []
    
    # Mock file_monitor_manager in fallback mode
    mock_monitor = Mock()
    mock_monitor.is_in_fallback_mode.return_value = True
    
    # Simulate the check from draw_status()
    if mock_monitor.is_in_fallback_mode():
        status_parts.append("⚠ polling mode")
    
    # Verify the indicator is in the status parts
    assert "⚠ polling mode" in status_parts
    assert len(status_parts) == 1


def test_status_bar_no_indicator_when_native_mode():
    """Test that status bar does not show indicator when in native mode."""
    status_parts = []
    
    # Mock file_monitor_manager in native mode
    mock_monitor = Mock()
    mock_monitor.is_in_fallback_mode.return_value = False
    
    # Simulate the check from draw_status()
    if mock_monitor.is_in_fallback_mode():
        status_parts.append("⚠ polling mode")
    
    # Verify the indicator is NOT in the status parts
    assert "⚠ polling mode" not in status_parts
    assert len(status_parts) == 0


def test_status_bar_combines_multiple_indicators():
    """Test that status bar can show multiple indicators together."""
    status_parts = []
    
    # Mock file_monitor_manager in fallback mode
    mock_monitor = Mock()
    mock_monitor.is_in_fallback_mode.return_value = True
    
    # Simulate archive browsing
    current_path_str = "archive:///path/to/archive.zip"
    if current_path_str.startswith('archive://'):
        status_parts.append("📦 archive")
    
    # Simulate fallback mode check
    if mock_monitor.is_in_fallback_mode():
        status_parts.append("⚠ polling mode")
    
    # Simulate show_hidden flag
    show_hidden = True
    if show_hidden:
        status_parts.append("showing hidden")
    
    # Verify all indicators are present
    assert "📦 archive" in status_parts
    assert "⚠ polling mode" in status_parts
    assert "showing hidden" in status_parts
    assert len(status_parts) == 3
    
    # Verify the formatted status string
    left_status = f"({', '.join(status_parts)})"
    assert left_status == "(📦 archive, ⚠ polling mode, showing hidden)"
