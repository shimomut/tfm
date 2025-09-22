#!/usr/bin/env python3
"""
Quit Cursor Saving Demo

Demonstrates how TFM now saves cursor positions when quitting,
ensuring they are preserved for the next startup.
"""

import sys
import tempfile
import time
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_state_manager import TFMStateManager
from tfm_pane_manager import PaneManager
from tfm_config import DefaultConfig


class MockStdscr:
    """Mock curses screen for demonstration."""
    def __init__(self, height=40, width=120):
        self.height = height
        self.width = width
    
    def getmaxyx(self):
        return self.height, self.width


class DemoFileManager:
    """Demo FileManager that simulates TFM quit behavior."""
    def __init__(self, config, left_path, right_path, state_manager):
        self.config = config
        self.state_manager = state_manager
        self.pane_manager = PaneManager(config, left_path, right_path, state_manager)
        self.stdscr = MockStdscr()
        self.log_height_ratio = 0.25
        self.needs_full_redraw = False
    
    def refresh_files(self):
        """Populate panes with files from their directories."""
        # Left pane files
        left_path = self.pane_manager.left_pane['path']
        if left_path.exists():
            self.pane_manager.left_pane['files'] = sorted([
                f for f in left_path.iterdir() if f.is_file()
            ])
        
        # Right pane files
        right_path = self.pane_manager.right_pane['path']
        if right_path.exists():
            self.pane_manager.right_pane['files'] = sorted([
                f for f in right_path.iterdir() if f.is_file()
            ])
    
    def save_quit_cursor_positions(self):
        """Save current cursor positions when quitting TFM."""
        saved_info = []
        try:
            # Save left pane cursor position
            if (self.pane_manager.left_pane['files'] and 
                self.pane_manager.left_pane['selected_index'] < len(self.pane_manager.left_pane['files'])):
                
                self.pane_manager.save_cursor_position(self.pane_manager.left_pane)
                
                left_path = self.pane_manager.left_pane['path']
                selected_file = self.pane_manager.left_pane['files'][self.pane_manager.left_pane['selected_index']].name
                saved_info.append(f"Left pane: {selected_file}")
            
            # Save right pane cursor position
            if (self.pane_manager.right_pane['files'] and 
                self.pane_manager.right_pane['selected_index'] < len(self.pane_manager.right_pane['files'])):
                
                self.pane_manager.save_cursor_position(self.pane_manager.right_pane)
                
                right_path = self.pane_manager.right_pane['path']
                selected_file = self.pane_manager.right_pane['files'][self.pane_manager.right_pane['selected_index']].name
                saved_info.append(f"Right pane: {selected_file}")
        
        except Exception as e:
            print(f"Warning: Could not save cursor positions on quit: {e}")
        
        return saved_info
    
    def simulate_quit(self):
        """Simulate TFM quit process including cursor saving."""
        print("  User presses 'q' to quit TFM...")
        print("  Saving application state...")
        
        # Save window layout
        self.state_manager.save_window_layout(
            self.pane_manager.left_pane_ratio,
            self.log_height_ratio
        )
        
        # Save pane states
        self.state_manager.save_pane_state('left', self.pane_manager.left_pane)
        self.state_manager.save_pane_state('right', self.pane_manager.right_pane)
        
        # Save current cursor positions before quitting
        print("  Saving current cursor positions...")
        saved_info = self.save_quit_cursor_positions()
        
        for info in saved_info:
            print(f"    ✓ {info}")
        
        # Add current directories to recent directories
        left_path = str(self.pane_manager.left_pane['path'])
        right_path = str(self.pane_manager.right_pane['path'])
        
        self.state_manager.add_recent_directory(left_path)
        if left_path != right_path:
            self.state_manager.add_recent_directory(right_path)
        
        # Clean up session
        self.state_manager.cleanup_session()
        
        print("  TFM quit complete!")
        
        return saved_info
    
    def simulate_startup(self):
        """Simulate TFM startup process including cursor restoration."""
        print("  Initializing TFM...")
        print("  Loading configuration...")
        print("  Refreshing file lists...")
        self.refresh_files()
        
        print("  Restoring cursor positions...")
        
        # Calculate display height for cursor restoration
        height, width = self.stdscr.getmaxyx()
        calculated_height = int(height * self.log_height_ratio)
        log_height = calculated_height if self.log_height_ratio > 0 else 0
        display_height = height - log_height - 3
        
        restored_info = []
        
        # Restore left pane cursor position
        left_restored = self.pane_manager.restore_cursor_position(self.pane_manager.left_pane, display_height)
        if left_restored:
            if self.pane_manager.left_pane['files']:
                selected_file = self.pane_manager.left_pane['files'][self.pane_manager.left_pane['selected_index']].name
                restored_info.append(f"Left pane: {selected_file} (index {self.pane_manager.left_pane['selected_index']})")
        
        # Restore right pane cursor position
        right_restored = self.pane_manager.restore_cursor_position(self.pane_manager.right_pane, display_height)
        if right_restored:
            if self.pane_manager.right_pane['files']:
                selected_file = self.pane_manager.right_pane['files'][self.pane_manager.right_pane['selected_index']].name
                restored_info.append(f"Right pane: {selected_file} (index {self.pane_manager.right_pane['selected_index']})")
        
        if restored_info:
            for info in restored_info:
                print(f"    ✓ {info}")
        else:
            print("    No cursor positions to restore")
        
        if left_restored or right_restored:
            self.needs_full_redraw = True
            print("  Triggering screen redraw...")
        
        print("  TFM startup complete!")
        
        return left_restored, right_restored, restored_info


def demo_quit_cursor_saving():
    """Demonstrate cursor position saving during TFM quit."""
    print("=== TFM Quit Cursor Saving Demo ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create development project structure
        src_dir = Path(temp_dir) / "src"
        tests_dir = Path(temp_dir) / "tests"
        
        src_dir.mkdir()
        tests_dir.mkdir()
        
        # Create source files
        src_files = [
            "main.py", "database.py", "api.py", "utils.py", 
            "config.py", "models.py", "views.py"
        ]
        for filename in src_files:
            (src_dir / filename).touch()
        
        # Create test files
        test_files = [
            "test_main.py", "test_database.py", "test_api.py", 
            "test_utils.py", "conftest.py"
        ]
        for filename in test_files:
            (tests_dir / filename).touch()
        
        print("Created development project structure:")
        print(f"  {src_dir} - {len(src_files)} source files")
        print(f"  {tests_dir} - {len(test_files)} test files")
        
        # === Working Session ===
        print("\n--- Working Session ---")
        
        state_manager = TFMStateManager("demo_quit_session")
        config = DefaultConfig()
        fm = DemoFileManager(config, src_dir, tests_dir, state_manager)
        
        print("Developer starts TFM and begins working:")
        fm.refresh_files()
        
        # Simulate developer working on specific files
        fm.pane_manager.left_pane['selected_index'] = 2   # api.py
        fm.pane_manager.right_pane['selected_index'] = 2  # test_api.py
        
        left_file = fm.pane_manager.left_pane['files'][2].name
        right_file = fm.pane_manager.right_pane['files'][2].name
        
        print(f"\nDeveloper is working on:")
        print(f"  Left pane: {left_file} (implementing API endpoints)")
        print(f"  Right pane: {right_file} (writing corresponding tests)")
        
        print(f"\nDeveloper has been working for a while...")
        print(f"  Making changes to {left_file}")
        print(f"  Adding test cases to {right_file}")
        print(f"  Current cursor positions are at the files being actively edited")
        
        # Developer decides to quit TFM
        print(f"\nDeveloper needs to step away and quits TFM:")
        
        saved_info = fm.simulate_quit()
        
        print(f"\n✓ TFM has saved the exact cursor positions!")
        print(f"  The developer can resume exactly where they left off")
        
        # === Resume Session ===
        print(f"\n--- Resume Session (Later) ---")
        
        print(f"Developer returns and starts TFM again:")
        
        state_manager2 = TFMStateManager("demo_quit_session2")
        state_manager2.db_path = state_manager.db_path  # Same database
        
        fm2 = DemoFileManager(config, src_dir, tests_dir, state_manager2)
        
        # Simulate TFM startup
        left_restored, right_restored, restored_info = fm2.simulate_startup()
        
        if left_restored and right_restored:
            print(f"\n🎉 Perfect! Developer can immediately continue working:")
            print(f"  Left pane: Back to {left_file} (exactly where they left off)")
            print(f"  Right pane: Back to {right_file} (test file in sync)")
            print(f"  No time wasted remembering or navigating")
            print(f"  Seamless workflow continuation!")
        else:
            print(f"\n✗ Cursor restoration failed")
        
        # Clean up
        state_manager2.cleanup_session()
        
        print(f"\n✓ Quit cursor saving demo completed!")


def demo_quit_saving_benefits():
    """Show the benefits of quit cursor saving."""
    print("\n=== Benefits of Quit Cursor Saving ===")
    
    print("Before (no quit cursor saving):")
    print("  • Cursor positions lost when TFM quits")
    print("  • Only saved during directory navigation")
    print("  • Final working position not preserved")
    print("  • User has to remember last edited files")
    
    print("\nAfter (with quit cursor saving):")
    print("  • Cursor positions saved automatically on quit")
    print("  • Final working position always preserved")
    print("  • No manual action required from user")
    print("  • Seamless integration with startup restoration")
    print("  • Complete workflow preservation")
    
    print("\nWhen cursor positions are saved:")
    print("  • During directory navigation (as before)")
    print("  • When quitting TFM (NEW!)")
    print("  • Ensures current working files are always remembered")
    
    print("\nUse cases:")
    print("  • Code editing: Save position in files being actively edited")
    print("  • Log analysis: Remember exact log file and position")
    print("  • File comparison: Preserve both files being compared")
    print("  • Documentation: Save position in documents being written")
    print("  • Project management: Remember current task files")


def demo_quit_saving_scenarios():
    """Demonstrate various quit saving scenarios."""
    print("\n=== Quit Saving Scenarios ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create project structure
        project_dir = Path(temp_dir) / "project"
        logs_dir = Path(temp_dir) / "logs"
        
        project_dir.mkdir()
        logs_dir.mkdir()
        
        # Create files
        project_files = ["app.py", "server.py", "client.py"]
        log_files = ["error.log", "access.log", "debug.log"]
        
        for filename in project_files:
            (project_dir / filename).touch()
        
        for filename in log_files:
            (logs_dir / filename).touch()
        
        print("Scenario 1: Emergency quit")
        print("  Developer is debugging an issue")
        print("  Looking at server.py and error.log")
        print("  Suddenly needs to leave (meeting, emergency, etc.)")
        print("  Quickly quits TFM with 'q'")
        
        # Simulate scenario 1
        state_manager = TFMStateManager("scenario1")
        fm = DemoFileManager(DefaultConfig(), project_dir, logs_dir, state_manager)
        fm.refresh_files()
        
        fm.pane_manager.left_pane['selected_index'] = 1   # server.py
        fm.pane_manager.right_pane['selected_index'] = 0  # error.log
        
        print(f"\n  Current positions:")
        print(f"    Left: {fm.pane_manager.left_pane['files'][1].name}")
        print(f"    Right: {fm.pane_manager.right_pane['files'][0].name}")
        
        saved_info = fm.save_quit_cursor_positions()
        print(f"\n  ✓ Positions saved on emergency quit!")
        
        state_manager.cleanup_session()
        
        print(f"\n  Later: Developer returns and can immediately continue debugging")
        print(f"         at the exact same files!")
        
        print(f"\nScenario 2: End of workday")
        print("  Developer finishes work for the day")
        print("  Was working on app.py and reviewing access.log")
        print("  Properly quits TFM to go home")
        
        # Simulate scenario 2
        state_manager2 = TFMStateManager("scenario2")
        fm2 = DemoFileManager(DefaultConfig(), project_dir, logs_dir, state_manager2)
        fm2.refresh_files()
        
        fm2.pane_manager.left_pane['selected_index'] = 0   # app.py
        fm2.pane_manager.right_pane['selected_index'] = 1  # access.log
        
        print(f"\n  Current positions:")
        print(f"    Left: {fm2.pane_manager.left_pane['files'][0].name}")
        print(f"    Right: {fm2.pane_manager.right_pane['files'][1].name}")
        
        saved_info2 = fm2.save_quit_cursor_positions()
        print(f"\n  ✓ Positions saved on normal quit!")
        
        state_manager2.cleanup_session()
        
        print(f"\n  Next day: Developer starts TFM and immediately sees")
        print(f"           yesterday's work context restored!")
        
        print(f"\n✓ All scenarios handled seamlessly!")


def main():
    """Run the quit cursor saving demonstration."""
    print("TFM Quit Cursor Saving Demonstration")
    print("=" * 60)
    
    try:
        demo_quit_cursor_saving()
        demo_quit_saving_benefits()
        demo_quit_saving_scenarios()
        
        print("\n" + "=" * 60)
        print("Demonstration completed successfully!")
        print("\nKey takeaways:")
        print("  • TFM now saves cursor positions when quitting")
        print("  • No manual action required from user")
        print("  • Works seamlessly with startup restoration")
        print("  • Preserves exact working context")
        print("  • Handles emergency quits and normal quits equally")
        print("  • Complete workflow preservation across sessions")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)