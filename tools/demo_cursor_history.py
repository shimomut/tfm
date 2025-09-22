#!/usr/bin/env python3
"""
Cursor History Persistence Demo

Demonstrates how TFM now saves and restores cursor positions across sessions.
"""

import sys
import tempfile
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_state_manager import TFMStateManager
from tfm_pane_manager import PaneManager
from tfm_config import DefaultConfig


def demo_cursor_history_persistence():
    """Demonstrate cursor history persistence across sessions."""
    print("=== Cursor History Persistence Demo ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test directory structure
        projects_dir = Path(temp_dir) / "projects"
        documents_dir = Path(temp_dir) / "documents"
        downloads_dir = Path(temp_dir) / "downloads"
        
        for directory in [projects_dir, documents_dir, downloads_dir]:
            directory.mkdir()
        
        # Create files in each directory
        project_files = ["main.py", "utils.py", "config.json", "README.md", "requirements.txt"]
        for filename in project_files:
            (projects_dir / filename).touch()
        
        document_files = ["report.docx", "notes.txt", "presentation.pptx", "data.csv"]
        for filename in document_files:
            (documents_dir / filename).touch()
        
        download_files = ["installer.exe", "archive.zip", "image.jpg", "video.mp4"]
        for filename in download_files:
            (downloads_dir / filename).touch()
        
        print("Created test directory structure:")
        print(f"  {projects_dir} - {len(project_files)} files")
        print(f"  {documents_dir} - {len(document_files)} files")
        print(f"  {downloads_dir} - {len(download_files)} files")
        
        # === Session 1: Navigate and set cursor positions ===
        print("\n--- Session 1: Setting cursor positions ---")
        
        # Create state manager and pane manager
        state_manager = TFMStateManager("cursor_demo_session1")
        config = DefaultConfig()
        pane_manager = PaneManager(config, projects_dir, documents_dir, state_manager)
        
        # Simulate browsing projects directory
        pane_manager.left_pane['files'] = [projects_dir / f for f in project_files]
        pane_manager.left_pane['selected_index'] = 2  # config.json
        print(f"Left pane: {projects_dir}")
        print(f"  Cursor at: {project_files[2]} (index {pane_manager.left_pane['selected_index']})")
        
        # Save cursor position for projects directory
        pane_manager.save_cursor_position(pane_manager.left_pane)
        
        # Simulate browsing documents directory
        pane_manager.right_pane['files'] = [documents_dir / f for f in document_files]
        pane_manager.right_pane['selected_index'] = 1  # notes.txt
        print(f"Right pane: {documents_dir}")
        print(f"  Cursor at: {document_files[1]} (index {pane_manager.right_pane['selected_index']})")
        
        # Save cursor position for documents directory
        pane_manager.save_cursor_position(pane_manager.right_pane)
        
        # Navigate to downloads directory in left pane
        pane_manager.left_pane['path'] = downloads_dir
        pane_manager.left_pane['files'] = [downloads_dir / f for f in download_files]
        pane_manager.left_pane['selected_index'] = 3  # video.mp4
        print(f"Left pane navigated to: {downloads_dir}")
        print(f"  Cursor at: {download_files[3]} (index {pane_manager.left_pane['selected_index']})")
        
        # Save cursor position for downloads directory
        pane_manager.save_cursor_position(pane_manager.left_pane)
        
        # Show saved cursor positions
        cursor_positions = state_manager.get_all_path_cursor_positions()
        print(f"\nSaved cursor positions:")
        for path, filename in cursor_positions.items():
            print(f"  {path} -> {filename}")
        
        # Clean up session 1
        state_manager.cleanup_session()
        print("Session 1 ended")
        
        # === Session 2: Restore cursor positions ===
        print("\n--- Session 2: Restoring cursor positions ---")
        
        # Create new state manager and pane manager (simulating restart)
        state_manager2 = TFMStateManager("cursor_demo_session2")
        pane_manager2 = PaneManager(config, projects_dir, documents_dir, state_manager2)
        
        # Test 1: Navigate to projects directory and restore cursor
        print(f"\nNavigating to: {projects_dir}")
        pane_manager2.left_pane['path'] = projects_dir
        pane_manager2.left_pane['files'] = [projects_dir / f for f in project_files]
        pane_manager2.left_pane['selected_index'] = 0  # Start at first file
        
        print(f"  Initial cursor at: {project_files[0]} (index 0)")
        
        # Restore cursor position
        restored = pane_manager2.restore_cursor_position(pane_manager2.left_pane, 20)
        if restored:
            restored_index = pane_manager2.left_pane['selected_index']
            restored_filename = project_files[restored_index]
            print(f"  ✓ Restored cursor to: {restored_filename} (index {restored_index})")
        else:
            print(f"  ✗ Could not restore cursor position")
        
        # Test 2: Navigate to documents directory and restore cursor
        print(f"\nNavigating to: {documents_dir}")
        pane_manager2.right_pane['path'] = documents_dir
        pane_manager2.right_pane['files'] = [documents_dir / f for f in document_files]
        pane_manager2.right_pane['selected_index'] = 0  # Start at first file
        
        print(f"  Initial cursor at: {document_files[0]} (index 0)")
        
        # Restore cursor position
        restored = pane_manager2.restore_cursor_position(pane_manager2.right_pane, 20)
        if restored:
            restored_index = pane_manager2.right_pane['selected_index']
            restored_filename = document_files[restored_index]
            print(f"  ✓ Restored cursor to: {restored_filename} (index {restored_index})")
        else:
            print(f"  ✗ Could not restore cursor position")
        
        # Test 3: Navigate to downloads directory and restore cursor
        print(f"\nNavigating to: {downloads_dir}")
        pane_manager2.left_pane['path'] = downloads_dir
        pane_manager2.left_pane['files'] = [downloads_dir / f for f in download_files]
        pane_manager2.left_pane['selected_index'] = 0  # Start at first file
        
        print(f"  Initial cursor at: {download_files[0]} (index 0)")
        
        # Restore cursor position
        restored = pane_manager2.restore_cursor_position(pane_manager2.left_pane, 20)
        if restored:
            restored_index = pane_manager2.left_pane['selected_index']
            restored_filename = download_files[restored_index]
            print(f"  ✓ Restored cursor to: {restored_filename} (index {restored_index})")
        else:
            print(f"  ✗ Could not restore cursor position")
        
        # Test 4: Navigate to a directory we haven't visited before
        print(f"\nNavigating to new directory: {temp_dir}")
        pane_manager2.right_pane['path'] = Path(temp_dir)
        pane_manager2.right_pane['files'] = [Path(temp_dir) / "projects", Path(temp_dir) / "documents", Path(temp_dir) / "downloads"]
        pane_manager2.right_pane['selected_index'] = 0
        
        print(f"  Initial cursor at: projects (index 0)")
        
        # Try to restore cursor position (should fail since we haven't been here)
        restored = pane_manager2.restore_cursor_position(pane_manager2.right_pane, 20)
        if restored:
            print(f"  ✓ Unexpectedly restored cursor position")
        else:
            print(f"  ✓ Correctly no cursor position to restore (new directory)")
        
        # Clean up session 2
        state_manager2.cleanup_session()
        print("Session 2 ended")
        
        print("\n✓ Cursor history persistence demo completed successfully!")


def demo_cursor_history_benefits():
    """Show the benefits of persistent cursor history."""
    print("\n=== Benefits of Persistent Cursor History ===")
    
    print("Before (in-memory cursor history):")
    print("  • Cursor positions lost when TFM restarts")
    print("  • Had to remember where you were in each directory")
    print("  • Inefficient navigation when returning to directories")
    
    print("\nAfter (persistent cursor history):")
    print("  • Cursor positions remembered across TFM sessions")
    print("  • Automatic restoration when entering directories")
    print("  • Seamless workflow continuation after restart")
    print("  • Shared cursor history across multiple TFM instances")
    print("  • Intelligent size management (keeps 100 most recent)")
    
    print("\nUse cases:")
    print("  • Working on a project, restart TFM, cursor returns to last edited file")
    print("  • Browsing logs, cursor remembers which log file you were examining")
    print("  • Managing downloads, cursor stays on the file you were working with")
    print("  • Code review workflow, cursor remembers position in each source directory")


def main():
    """Run the cursor history demonstration."""
    print("TFM Cursor History Persistence Demonstration")
    print("=" * 60)
    
    try:
        demo_cursor_history_persistence()
        demo_cursor_history_benefits()
        
        print("\n" + "=" * 60)
        print("Demonstration completed successfully!")
        print("\nThe cursor history is now persistent and will survive TFM restarts.")
        print("This improves the user experience by maintaining navigation context.")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)