#!/usr/bin/env python3
"""
Startup Cursor Restoration Demo

Demonstrates how TFM now restores cursor positions when starting up,
not just when navigating between directories.
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
    """Demo FileManager that simulates TFM startup behavior."""
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
    
    def restore_startup_cursor_positions(self):
        """Restore cursor positions for both panes during startup."""
        try:
            # Calculate display height for cursor restoration
            height, width = self.stdscr.getmaxyx()
            calculated_height = int(height * self.log_height_ratio)
            log_height = calculated_height if self.log_height_ratio > 0 else 0
            display_height = height - log_height - 3
            
            restored_info = []
            
            # Restore left pane cursor position
            left_restored = self.pane_manager.restore_cursor_position(self.pane_manager.left_pane, display_height)
            if left_restored:
                left_path = self.pane_manager.left_pane['path']
                if self.pane_manager.left_pane['files']:
                    selected_file = self.pane_manager.left_pane['files'][self.pane_manager.left_pane['selected_index']].name
                    restored_info.append(f"Left pane: {selected_file} (index {self.pane_manager.left_pane['selected_index']})")
            
            # Restore right pane cursor position
            right_restored = self.pane_manager.restore_cursor_position(self.pane_manager.right_pane, display_height)
            if right_restored:
                right_path = self.pane_manager.right_pane['path']
                if self.pane_manager.right_pane['files']:
                    selected_file = self.pane_manager.right_pane['files'][self.pane_manager.right_pane['selected_index']].name
                    restored_info.append(f"Right pane: {selected_file} (index {self.pane_manager.right_pane['selected_index']})")
            
            # If either cursor was restored, trigger a redraw
            if left_restored or right_restored:
                self.needs_full_redraw = True
            
            return left_restored, right_restored, restored_info
                
        except Exception as e:
            print(f"Warning: Could not restore startup cursor positions: {e}")
            return False, False, []
    
    def simulate_startup(self):
        """Simulate TFM startup process including cursor restoration."""
        print("  Initializing TFM...")
        print("  Loading configuration...")
        print("  Refreshing file lists...")
        self.refresh_files()
        
        print("  Restoring cursor positions...")
        left_restored, right_restored, restored_info = self.restore_startup_cursor_positions()
        
        if restored_info:
            for info in restored_info:
                print(f"    ✓ {info}")
        else:
            print("    No cursor positions to restore")
        
        if self.needs_full_redraw:
            print("  Triggering screen redraw...")
        
        print("  TFM startup complete!")
        
        return left_restored, right_restored


def demo_startup_cursor_restoration():
    """Demonstrate cursor position restoration during TFM startup."""
    print("=== TFM Startup Cursor Restoration Demo ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create project directory structure
        projects_dir = Path(temp_dir) / "projects"
        documents_dir = Path(temp_dir) / "documents"
        
        projects_dir.mkdir()
        documents_dir.mkdir()
        
        # Create project files
        project_files = [
            "main.py", "utils.py", "config.json", "README.md", 
            "requirements.txt", "setup.py", "tests.py"
        ]
        for filename in project_files:
            (projects_dir / filename).touch()
        
        # Create document files
        document_files = [
            "notes.txt", "report.docx", "presentation.pptx", 
            "data.csv", "analysis.py"
        ]
        for filename in document_files:
            (documents_dir / filename).touch()
        
        print("Created test directory structure:")
        print(f"  {projects_dir} - {len(project_files)} files")
        print(f"  {documents_dir} - {len(document_files)} files")
        
        # === TFM Session 1: Work and set cursor positions ===
        print("\n--- TFM Session 1: Working Session ---")
        
        state_manager = TFMStateManager("demo_startup_session1")
        config = DefaultConfig()
        fm1 = DemoFileManager(config, projects_dir, documents_dir, state_manager)
        
        print("Starting TFM...")
        fm1.refresh_files()
        
        # Simulate user working and navigating
        print("\nUser working in TFM:")
        
        # User navigates to specific files
        fm1.pane_manager.left_pane['selected_index'] = 4   # requirements.txt
        fm1.pane_manager.right_pane['selected_index'] = 2  # presentation.pptx
        
        left_file = fm1.pane_manager.left_pane['files'][4].name
        right_file = fm1.pane_manager.right_pane['files'][2].name
        
        print(f"  Left pane: Working on {left_file}")
        print(f"  Right pane: Reviewing {right_file}")
        
        # Save cursor positions (happens automatically during navigation)
        fm1.pane_manager.save_cursor_position(fm1.pane_manager.left_pane)
        fm1.pane_manager.save_cursor_position(fm1.pane_manager.right_pane)
        
        print(f"  Cursor positions saved automatically")
        
        # User exits TFM
        print("\nUser exits TFM (Ctrl+Q)")
        state_manager.cleanup_session()
        
        # === TFM Session 2: Restart and restore ===
        print("\n--- TFM Session 2: Restart ---")
        
        print("User restarts TFM...")
        
        state_manager2 = TFMStateManager("demo_startup_session2")
        state_manager2.db_path = state_manager.db_path  # Same database
        
        fm2 = DemoFileManager(config, projects_dir, documents_dir, state_manager2)
        
        # Simulate TFM startup process
        left_restored, right_restored = fm2.simulate_startup()
        
        # Verify restoration
        if left_restored and right_restored:
            current_left = fm2.pane_manager.left_pane['files'][fm2.pane_manager.left_pane['selected_index']].name
            current_right = fm2.pane_manager.right_pane['files'][fm2.pane_manager.right_pane['selected_index']].name
            
            print(f"\n✓ User can continue exactly where they left off!")
            print(f"  Left pane: Back to {current_left}")
            print(f"  Right pane: Back to {current_right}")
        else:
            print("\n✗ Cursor restoration failed")
        
        # Clean up
        state_manager2.cleanup_session()
        
        print("\n✓ Startup cursor restoration demo completed!")


def demo_startup_benefits():
    """Show the benefits of startup cursor restoration."""
    print("\n=== Benefits of Startup Cursor Restoration ===")
    
    print("Before (no startup restoration):")
    print("  • TFM always starts with cursor at first file")
    print("  • User has to remember where they were working")
    print("  • Need to manually navigate back to previous files")
    print("  • Workflow interruption after restart")
    
    print("\nAfter (with startup restoration):")
    print("  • TFM restores cursor to last working position")
    print("  • Seamless continuation of previous work session")
    print("  • No manual navigation required")
    print("  • Maintains separate positions for left and right panes")
    print("  • Automatic scroll adjustment for visibility")
    print("  • Graceful handling of missing files")
    
    print("\nUse cases:")
    print("  • Code editing: Return to the exact file you were editing")
    print("  • Log analysis: Continue from where you stopped reviewing logs")
    print("  • File comparison: Maintain context for both files being compared")
    print("  • Project management: Resume work on specific project files")
    print("  • Documentation: Return to the document you were reading")


def demo_startup_workflow():
    """Demonstrate a realistic workflow with startup restoration."""
    print("\n=== Realistic Workflow Demo ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a realistic project structure
        project_root = Path(temp_dir) / "my_project"
        src_dir = project_root / "src"
        docs_dir = project_root / "docs"
        
        project_root.mkdir()
        src_dir.mkdir()
        docs_dir.mkdir()
        
        # Create source files
        src_files = ["main.py", "database.py", "api.py", "utils.py", "config.py"]
        for filename in src_files:
            (src_dir / filename).touch()
        
        # Create documentation files
        doc_files = ["README.md", "API.md", "INSTALL.md", "CHANGELOG.md"]
        for filename in doc_files:
            (docs_dir / filename).touch()
        
        print("Scenario: Developer working on a Python project")
        print(f"Project structure:")
        print(f"  {src_dir} - Source code files")
        print(f"  {docs_dir} - Documentation files")
        
        # === Day 1: Working session ===
        print("\n--- Day 1: Working Session ---")
        
        state_manager = TFMStateManager("workflow_day1")
        config = DefaultConfig()
        fm = DemoFileManager(config, src_dir, docs_dir, state_manager)
        fm.refresh_files()
        
        print("Developer starts TFM and begins working:")
        
        # Developer works on database.py and API documentation
        fm.pane_manager.left_pane['selected_index'] = 1   # database.py
        fm.pane_manager.right_pane['selected_index'] = 1  # API.md
        
        left_file = fm.pane_manager.left_pane['files'][1].name
        right_file = fm.pane_manager.right_pane['files'][1].name
        
        print(f"  Left pane: Editing {left_file}")
        print(f"  Right pane: Updating {right_file}")
        
        # Save positions
        fm.pane_manager.save_cursor_position(fm.pane_manager.left_pane)
        fm.pane_manager.save_cursor_position(fm.pane_manager.right_pane)
        
        print("  Working... making changes...")
        print("  End of day - developer closes TFM")
        
        state_manager.cleanup_session()
        
        # === Day 2: Resume work ===
        print("\n--- Day 2: Resume Work ---")
        
        print("Developer starts TFM the next day:")
        
        state_manager2 = TFMStateManager("workflow_day2")
        state_manager2.db_path = state_manager.db_path
        
        fm2 = DemoFileManager(config, src_dir, docs_dir, state_manager2)
        
        # Simulate startup
        print("\nTFM Startup Process:")
        left_restored, right_restored = fm2.simulate_startup()
        
        if left_restored and right_restored:
            current_left = fm2.pane_manager.left_pane['files'][fm2.pane_manager.left_pane['selected_index']].name
            current_right = fm2.pane_manager.right_pane['files'][fm2.pane_manager.right_pane['selected_index']].name
            
            print(f"\n🎉 Perfect! Developer can immediately continue working:")
            print(f"  Left pane: {current_left} (exactly where they left off)")
            print(f"  Right pane: {current_right} (documentation in sync)")
            print(f"  No time wasted remembering or navigating back")
            print(f"  Instant productivity!")
        
        state_manager2.cleanup_session()
        
        print("\n✓ Realistic workflow demo completed!")


def main():
    """Run the startup cursor restoration demonstration."""
    print("TFM Startup Cursor Restoration Demonstration")
    print("=" * 60)
    
    try:
        demo_startup_cursor_restoration()
        demo_startup_benefits()
        demo_startup_workflow()
        
        print("\n" + "=" * 60)
        print("Demonstration completed successfully!")
        print("\nKey takeaways:")
        print("  • TFM now remembers cursor positions across restarts")
        print("  • Separate histories for left and right panes")
        print("  • Automatic restoration during startup")
        print("  • Seamless workflow continuation")
        print("  • Improved productivity and user experience")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)