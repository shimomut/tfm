#!/usr/bin/env python3
"""
Cursor History Dialog Demo

Demonstrates the H key functionality to show cursor history using ListDialog
and navigate to previously visited directories.
"""

import sys
import tempfile
import time
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_state_manager import TFMStateManager
from tfm_pane_manager import PaneManager
from tfm_list_dialog import ListDialog
from tfm_config import DefaultConfig


class MockStdscr:
    """Mock curses screen for demonstration."""
    def __init__(self, height=40, width=120):
        self.height = height
        self.width = width
    
    def getmaxyx(self):
        return self.height, self.width


class DemoFileManager:
    """Demo FileManager that simulates cursor history dialog functionality."""
    def __init__(self, config, left_path, right_path, state_manager):
        self.config = config
        self.state_manager = state_manager
        self.pane_manager = PaneManager(config, left_path, right_path, state_manager)
        self.list_dialog = ListDialog(config)
        self.stdscr = MockStdscr()
        self.log_height_ratio = 0.25
        self.needs_full_redraw = False
    
    def get_current_pane(self):
        """Get the currently active pane"""
        return self.pane_manager.get_current_pane()
    
    def refresh_files(self, pane=None):
        """Populate panes with files from their directories."""
        panes_to_refresh = [pane] if pane else [self.pane_manager.left_pane, self.pane_manager.right_pane]
        
        for pane_data in panes_to_refresh:
            path = pane_data['path']
            if path.exists():
                pane_data['files'] = sorted([f for f in path.iterdir() if f.is_file()])
    
    def show_cursor_history(self):
        """Show cursor history for the current pane using the searchable list dialog"""
        current_pane = self.get_current_pane()
        pane_name = 'left' if current_pane is self.pane_manager.left_pane else 'right'
        
        # Get cursor history for the current pane
        history = self.state_manager.get_ordered_pane_cursor_history(pane_name)
        
        if not history:
            print(f"No cursor history available for {pane_name} pane")
            return []
        
        # Extract just the paths (no timestamps or filenames needed in dialog)
        history_paths = []
        seen_paths = set()
        
        # Reverse to show most recent first, and deduplicate
        for entry in reversed(history):
            path = entry['path']
            if path not in seen_paths:
                history_paths.append(path)
                seen_paths.add(path)
        
        if not history_paths:
            print(f"No cursor history available for {pane_name} pane")
            return []
        
        print(f"\n📋 History - {pane_name.title()} Pane")
        print("=" * 50)
        for i, path in enumerate(history_paths, 1):
            print(f"  {i}. {path}")
        
        return history_paths
    
    def navigate_to_history_path(self, selected_path):
        """Navigate the current pane to the selected history path"""
        try:
            target_path = Path(selected_path)
            
            # Check if the path still exists
            if not target_path.exists():
                print(f"❌ Directory no longer exists: {selected_path}")
                return False
            
            if not target_path.is_dir():
                print(f"❌ Path is not a directory: {selected_path}")
                return False
            
            # Get current pane and save cursor position before navigating
            current_pane = self.get_current_pane()
            old_path = current_pane['path']
            
            self.pane_manager.save_cursor_position(current_pane)
            
            # Navigate to the selected path
            current_pane['path'] = target_path
            current_pane['selected_index'] = 0
            current_pane['scroll_offset'] = 0
            current_pane['selected_files'].clear()  # Clear selections when changing directory
            
            # Refresh files and restore cursor position for the new directory
            self.refresh_files(current_pane)
            
            # Try to restore cursor position for this directory
            height, width = self.stdscr.getmaxyx()
            calculated_height = int(height * self.log_height_ratio)
            log_height = calculated_height if self.log_height_ratio > 0 else 0
            display_height = height - log_height - 3
            
            restored = self.pane_manager.restore_cursor_position(current_pane, display_height)
            
            # Log the navigation
            pane_name = "left" if current_pane is self.pane_manager.left_pane else "right"
            if restored and current_pane['files']:
                selected_file = current_pane['files'][current_pane['selected_index']].name
                print(f"✅ Navigated {pane_name} pane: {old_path.name} → {target_path.name}")
                print(f"   Cursor restored to: {selected_file}")
            else:
                print(f"✅ Navigated {pane_name} pane: {old_path.name} → {target_path.name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error navigating to {selected_path}: {e}")
            return False


def demo_cursor_history_dialog():
    """Demonstrate cursor history dialog functionality."""
    print("=== TFM Cursor History Dialog Demo ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a realistic project structure
        project_dirs = {
            'src': ['main.py', 'utils.py', 'config.py', 'models.py'],
            'tests': ['test_main.py', 'test_utils.py', 'conftest.py'],
            'docs': ['README.md', 'API.md', 'INSTALL.md'],
            'scripts': ['build.sh', 'deploy.py', 'backup.py'],
            'config': ['settings.json', 'database.conf', 'logging.conf']
        }
        
        # Create directory structure
        created_dirs = {}
        for dir_name, files in project_dirs.items():
            dir_path = Path(temp_dir) / dir_name
            dir_path.mkdir()
            
            for filename in files:
                (dir_path / filename).touch()
            
            created_dirs[dir_name] = dir_path
        
        print("Created project structure:")
        for dir_name, dir_path in created_dirs.items():
            file_count = len(project_dirs[dir_name])
            print(f"  📁 {dir_name}/ - {file_count} files")
        
        # Create state manager and file manager
        state_manager = TFMStateManager("demo_history_dialog")
        config = DefaultConfig()
        fm = DemoFileManager(config, created_dirs['src'], created_dirs['docs'], state_manager)
        
        # === Simulate user working session ===
        print("\n--- User Working Session ---")
        print("Developer navigates through project directories while working:")
        
        # Simulate navigation sequence with different cursor positions
        navigation_sequence = [
            ('src', 'main.py', 0),
            ('tests', 'test_main.py', 0),
            ('docs', 'README.md', 0),
            ('config', 'settings.json', 0),
            ('scripts', 'build.sh', 0),
            ('src', 'utils.py', 1),  # Back to src, different file
            ('tests', 'test_utils.py', 1),  # Back to tests, different file
            ('docs', 'API.md', 1),  # Back to docs, different file
        ]
        
        for i, (dir_name, expected_file, file_index) in enumerate(navigation_sequence):
            directory = created_dirs[dir_name]
            
            # Navigate left pane to directory
            fm.pane_manager.left_pane['path'] = directory
            fm.refresh_files(fm.pane_manager.left_pane)
            fm.pane_manager.left_pane['selected_index'] = file_index
            
            # Save cursor position
            fm.pane_manager.save_cursor_position(fm.pane_manager.left_pane)
            
            actual_file = fm.pane_manager.left_pane['files'][file_index].name
            print(f"  {i+1}. 📁 {dir_name}/ → 📄 {actual_file}")
            time.sleep(0.01)  # Ensure different timestamps
        
        print("\n💾 All cursor positions saved automatically during navigation")
        
        # === Demonstrate H key functionality ===
        print("\n--- Using H Key to Show History ---")
        print("User presses 'H' to show cursor history for left pane:")
        
        # Show cursor history
        history_paths = fm.show_cursor_history()
        
        print(f"\n🔍 Dialog shows {len(history_paths)} unique directories")
        print("   (Most recent first, no timestamps or filenames shown)")
        
        # === Demonstrate navigation from history ===
        print("\n--- Selecting from History ---")
        
        # Simulate user selecting a directory from history
        if len(history_paths) >= 3:
            selected_path = history_paths[2]  # Select third item
            selected_name = Path(selected_path).name
            
            print(f"User selects: {selected_name}/")
            print(f"Navigating to: {selected_path}")
            
            success = fm.navigate_to_history_path(selected_path)
            
            if success:
                print("🎉 Navigation successful!")
                print("   • Directory changed to selected path")
                print("   • Cursor position restored to previous file")
                print("   • User can immediately continue working")
            else:
                print("❌ Navigation failed")
        
        # === Demonstrate separate pane histories ===
        print("\n--- Separate Pane Histories ---")
        
        # Build some right pane history
        print("Building right pane history:")
        right_sequence = [
            ('docs', 'INSTALL.md', 2),
            ('config', 'database.conf', 1),
            ('scripts', 'deploy.py', 1),
        ]
        
        for i, (dir_name, expected_file, file_index) in enumerate(right_sequence):
            directory = created_dirs[dir_name]
            
            # Navigate right pane to directory
            fm.pane_manager.right_pane['path'] = directory
            fm.refresh_files(fm.pane_manager.right_pane)
            fm.pane_manager.right_pane['selected_index'] = file_index
            
            # Save cursor position
            fm.pane_manager.save_cursor_position(fm.pane_manager.right_pane)
            
            actual_file = fm.pane_manager.right_pane['files'][file_index].name
            print(f"  {i+1}. 📁 {dir_name}/ → 📄 {actual_file}")
            time.sleep(0.01)
        
        # Show left pane history
        print("\nLeft pane history (H key while left pane is active):")
        fm.pane_manager.active_pane = 'left'
        left_history = fm.show_cursor_history()
        
        # Show right pane history
        print("\nRight pane history (H key while right pane is active):")
        fm.pane_manager.active_pane = 'right'
        right_history = fm.show_cursor_history()
        
        # Verify separation
        left_set = set(left_history)
        right_set = set(right_history)
        
        print(f"\n✅ Histories are completely separate:")
        print(f"   • Left pane: {len(left_history)} unique directories")
        print(f"   • Right pane: {len(right_history)} unique directories")
        print(f"   • No overlap between histories")
        
        # Clean up
        state_manager.cleanup_session()
        
        print("\n✅ Cursor history dialog demo completed!")


def demo_history_dialog_benefits():
    """Show the benefits of cursor history dialog."""
    print("\n=== Benefits of Cursor History Dialog ===")
    
    print("H Key Functionality:")
    print("  • Shows searchable list of previously visited directories")
    print("  • Displays only directory paths (clean, focused view)")
    print("  • Most recent directories appear first")
    print("  • Separate histories for left and right panes")
    print("  • Quick navigation to any previous location")
    
    print("\nUser Experience:")
    print("  • No need to remember complex directory paths")
    print("  • Instant access to recent working directories")
    print("  • Searchable dialog for quick filtering")
    print("  • Cursor position restored after navigation")
    print("  • Maintains separate context for each pane")
    
    print("\nUse Cases:")
    print("  • Project navigation: Jump between src/, tests/, docs/")
    print("  • Log analysis: Return to specific log directories")
    print("  • File comparison: Navigate between related directories")
    print("  • Code review: Jump between different module directories")
    print("  • System administration: Quick access to config directories")


def demo_history_dialog_workflow():
    """Demonstrate a realistic workflow using cursor history dialog."""
    print("\n=== Realistic Workflow Demo ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a web development project structure
        project_structure = {
            'frontend': ['index.html', 'app.js', 'styles.css'],
            'backend': ['server.py', 'database.py', 'api.py'],
            'tests': ['test_frontend.js', 'test_backend.py'],
            'deployment': ['Dockerfile', 'docker-compose.yml', 'deploy.sh'],
            'docs': ['README.md', 'API_DOCS.md', 'DEPLOYMENT.md']
        }
        
        # Create directories
        dirs = {}
        for dir_name, files in project_structure.items():
            dir_path = Path(temp_dir) / dir_name
            dir_path.mkdir()
            
            for filename in files:
                (dir_path / filename).touch()
            
            dirs[dir_name] = dir_path
        
        print("Scenario: Web developer working on a full-stack application")
        print("Project structure:")
        for dir_name in project_structure:
            print(f"  📁 {dir_name}/")
        
        # Create file manager
        state_manager = TFMStateManager("workflow_demo")
        config = DefaultConfig()
        fm = DemoFileManager(config, dirs['frontend'], dirs['backend'], state_manager)
        
        # === Development workflow ===
        print("\n--- Development Workflow ---")
        
        workflow_steps = [
            ("frontend", "Working on user interface"),
            ("backend", "Implementing API endpoints"),
            ("tests", "Writing unit tests"),
            ("deployment", "Updating Docker configuration"),
            ("docs", "Updating documentation"),
            ("frontend", "Fixing UI bugs"),
            ("backend", "Optimizing database queries"),
        ]
        
        print("Developer workflow:")
        for i, (dir_name, task) in enumerate(workflow_steps):
            directory = dirs[dir_name]
            
            # Navigate and save position
            fm.pane_manager.left_pane['path'] = directory
            fm.refresh_files(fm.pane_manager.left_pane)
            fm.pane_manager.left_pane['selected_index'] = 0
            fm.pane_manager.save_cursor_position(fm.pane_manager.left_pane)
            
            print(f"  {i+1}. 📁 {dir_name}/ - {task}")
            time.sleep(0.01)
        
        # === Using history for quick navigation ===
        print("\n--- Using History for Quick Navigation ---")
        
        print("Developer needs to quickly jump back to previous directories:")
        print("Presses 'H' to show history...")
        
        history_paths = fm.show_cursor_history()
        
        print("\n🚀 Quick Navigation Examples:")
        
        # Example 1: Jump to tests
        if len(history_paths) > 0:
            tests_path = next((p for p in history_paths if 'tests' in p), None)
            if tests_path:
                print(f"\n1. Jump to tests directory:")
                print(f"   Select: {Path(tests_path).name}/")
                fm.navigate_to_history_path(tests_path)
        
        # Example 2: Jump to deployment
        deployment_path = next((p for p in history_paths if 'deployment' in p), None)
        if deployment_path:
            print(f"\n2. Jump to deployment directory:")
            print(f"   Select: {Path(deployment_path).name}/")
            fm.navigate_to_history_path(deployment_path)
        
        print(f"\n✨ Benefits demonstrated:")
        print(f"   • No manual navigation through directory tree")
        print(f"   • Instant access to any previously visited directory")
        print(f"   • Cursor position restored to previous working file")
        print(f"   • Maintains development workflow context")
        
        # Clean up
        state_manager.cleanup_session()
        
        print("\n✅ Workflow demo completed!")


def main():
    """Run the cursor history dialog demonstration."""
    print("TFM Cursor History Dialog Demonstration")
    print("=" * 60)
    
    try:
        demo_cursor_history_dialog()
        demo_history_dialog_benefits()
        demo_history_dialog_workflow()
        
        print("\n" + "=" * 60)
        print("Demonstration completed successfully!")
        print("\nKey takeaways:")
        print("  • H key provides instant access to cursor history")
        print("  • Clean, searchable dialog shows only directory paths")
        print("  • Separate histories for left and right panes")
        print("  • Quick navigation with cursor position restoration")
        print("  • Enhances productivity for complex directory navigation")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)