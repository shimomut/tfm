#!/usr/bin/env python3
"""
Demo: SingleLineTextEdit Clipboard Paste Feature

This demo demonstrates the clipboard paste functionality in SingleLineTextEdit,
which is used throughout TFM for text input fields (rename, create file/directory,
filter, search, etc.).

The paste feature allows users to paste text from the system clipboard using
Cmd+V (macOS) or Ctrl+V (other platforms).

Features:
- Paste text at cursor position
- Multiline clipboard text is converted to single line (newlines → spaces)
- Respects max_length constraints
- Only works in desktop mode (clipboard not available in terminal)

Usage:
    python demo/demo_single_line_text_edit_paste.py

Note: This demo only works in desktop mode (CoreGraphics backend).
"""

import sys
import os

# Add src and ttk to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ttk'))

from tfm_backend_selector import select_backend
from tfm_single_line_text_edit import SingleLineTextEdit
from ttk import KeyEvent, KeyCode, ModifierKey, CharEvent


def main():
    """Run the clipboard paste demo"""
    
    print("=" * 80)
    print("SingleLineTextEdit Clipboard Paste Demo")
    print("=" * 80)
    print()
    print("This demo shows clipboard paste functionality in text input fields.")
    print()
    print("The paste feature is used in:")
    print("  - Rename file/directory (F2)")
    print("  - Create file (F7) / Create directory (F8)")
    print("  - Filter files (Ctrl+F)")
    print("  - Search dialog")
    print("  - Batch rename dialog")
    print()
    print("How it works:")
    print("  - Press Cmd+V / Ctrl+V to paste clipboard text")
    print("  - Text is inserted at the cursor position")
    print("  - Multiline text is converted to single line (newlines → spaces)")
    print("  - Respects max_length constraints (truncates if needed)")
    print()
    print("=" * 80)
    print()
    
    # Simple unit test demonstration
    print("Unit Test Demonstration:")
    print("-" * 80)
    print()
    
    # Create mock renderer
    from unittest.mock import Mock
    mock_renderer = Mock()
    mock_renderer.supports_clipboard.return_value = True
    mock_renderer.get_clipboard_text.return_value = "Hello from clipboard!"
    
    print("1. Creating a SingleLineTextEdit with initial text...")
    editor = SingleLineTextEdit("Initial text: ", renderer=mock_renderer)
    print(f"   Text: '{editor.get_text()}'")
    print(f"   Cursor position: {editor.get_cursor_pos()}")
    
    print()
    print("2. Simulating Cmd+V paste...")
    # Create a mock KeyEvent for Cmd+V
    from unittest.mock import Mock
    from ttk import KeyEvent
    event = Mock(spec=KeyEvent)
    event.char = 'v'
    event.key_code = None
    event.has_modifier = Mock(return_value=True)
    
    result = editor.handle_key(event)
    
    if result:
        print(f"   ✓ Paste successful!")
        print(f"   New text: '{editor.get_text()}'")
        print(f"   New cursor position: {editor.get_cursor_pos()}")
    else:
        print("   ✗ Paste failed")
        return 1
    
    print()
    print("3. Testing multiline clipboard text...")
    multiline_text = "Line 1\nLine 2\nLine 3"
    mock_renderer.get_clipboard_text.return_value = multiline_text
    print(f"   Clipboard contains multiline text:")
    for line in multiline_text.split('\n'):
        print(f"     '{line}'")
    
    editor2 = SingleLineTextEdit("", renderer=mock_renderer)
    result = editor2.handle_key(event)
    
    if result:
        print(f"   ✓ Paste successful!")
        print(f"   Result (newlines → spaces): '{editor2.get_text()}'")
    else:
        print("   ✗ Paste failed")
    
    print()
    print("4. Testing max_length constraint...")
    mock_renderer.get_clipboard_text.return_value = "Very long text that exceeds limit"
    editor3 = SingleLineTextEdit("Start: ", max_length=20, renderer=mock_renderer)
    print(f"   Initial text: '{editor3.get_text()}' (length: {len(editor3.get_text())})")
    print(f"   Max length: 20")
    print(f"   Available space: {20 - len(editor3.get_text())} characters")
    
    result = editor3.handle_key(event)
    
    if result:
        print(f"   ✓ Paste successful (truncated to fit)!")
        print(f"   Result: '{editor3.get_text()}' (length: {len(editor3.get_text())})")
    else:
        print("   ✗ Paste failed")
    
    print()
    print("-" * 80)
    print()
    print("Demo completed successfully!")
    print()
    print("To see this in action in TFM:")
    print("  1. Run TFM in desktop mode: python tfm.py --desktop")
    print("  2. Copy some text to clipboard")
    print("  3. Press F2 to rename a file")
    print("  4. Press Cmd+V / Ctrl+V to paste")
    print()
    
    return 0
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
