#!/usr/bin/env python3

import sys
import tempfile
import time
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_state_manager import TFMStateManager
from tfm_pane_manager import PaneManager
from tfm_config import DefaultConfig


class DemoConfig(DefaultConfig):
    """Demo configuration"""
    def __init__(self):
        super().__init__()
        self.MAX_CURSOR_HISTORY_ENTRIES = 15


def demo_cursor_history_tab_switching():
    """Demonstrate TAB key switching between left and right pane histories"""
    print("TFM Cursor History TAB Switching Demonstration")
    print("=" * 60)
    print("=== Enhanced Cursor History Dialog with TAB Switching ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a realistic project structure
        project_dirs = {
            'frontend': ['components', 'pages', 'styles', 'utils'],
            'backend': ['api', 'models', 'services', 'middleware'],
            'tests': ['unit', 'integration', 'e2e'],
            'docs': ['api', 'user-guide', 'development'],
            'config': ['development', 'production', 'testing']
        }
        
        created_dirs = []
        for main_dir, sub_dirs in project_dirs.items():
            main_path = Path(temp_dir) / main_dir
            main_path.mkdir()
            created_dirs.append(main_path)
            
            for sub_dir in sub_dirs:
                sub_path = main_path / sub_dir
                sub_path.mkdir()
                # Create some files
                for i in range(3):
                    (sub_path / f"file_{i}.py").touch()
        
        print("Created project structure:")
        for main_dir in project_dirs.keys():
            print(f"  📁 {main_dir}/")
        print()
        
        # Create state manager and pane manager
        db_path = Path(temp_dir) / "demo_state.db"
        state_manager = TFMStateManager("demo_tab_switching")
        state_manager.db_path = db_path
        state_manager._initialize_database()
        
        config = DemoConfig()
        pane_manager = PaneManager(config, created_dirs[0], created_dirs[1], state_manager)
        
        # Simulate developer workflow - left pane navigation
        print("--- Left Pane Navigation History ---")
        left_workflow = [
            (created_dirs[0], "App.py"),           # frontend
            (created_dirs[2], "test_auth.py"),     # tests  
            (created_dirs[1], "user_model.py"),    # backend
            (created_dirs[3], "README.md"),        # docs
            (created_dirs[0], "Login.py"),         # frontend
            (created_dirs[4], "database.conf"),    # config
            (created_dirs[1], "auth_service.py"),  # backend
        ]
        
        for i, (directory, filename) in enumerate(left_workflow):
            pane_manager.left_pane['path'] = directory
            pane_manager.left_pane['files'] = [directory / filename]
            pane_manager.left_pane['selected_index'] = 0
            pane_manager.save_cursor_position(pane_manager.left_pane)
            print(f"  {i+1}. 📁 {directory.name}/ → 📄 {filename}")
            time.sleep(0.01)
        
        print()
        
        # Simulate developer workflow - right pane navigation  
        print("--- Right Pane Navigation History ---")
        right_workflow = [
            (created_dirs[4], "app.conf"),         # config
            (created_dirs[3], "API.md"),           # docs
            (created_dirs[2], "test_models.py"),   # tests
            (created_dirs[1], "database.py"),      # backend
            (created_dirs[0], "Header.py"),        # frontend
        ]
        
        for i, (directory, filename) in enumerate(right_workflow):
            pane_manager.right_pane['path'] = directory
            pane_manager.right_pane['files'] = [directory / filename]
            pane_manager.right_pane['selected_index'] = 0
            pane_manager.save_cursor_position(pane_manager.right_pane)
            print(f"  {i+1}. 📁 {directory.name}/ → 📄 {filename}")
            time.sleep(0.01)
        
        print()
        
        # Show the enhanced cursor history dialog functionality
        print("--- Enhanced Cursor History Dialog ---")
        print("🔥 NEW FEATURE: TAB Key Switching Between Pane Histories")
        print()
        
        # Get histories for both panes
        left_history = state_manager.get_ordered_pane_cursor_history('left')
        right_history = state_manager.get_ordered_pane_cursor_history('right')
        
        # Show left pane history
        print("📋 History - Left")
        print("💡 Help: ↑↓:select  Enter:choose  TAB:switch to Right  Type:search  ESC:cancel")
        print("=" * 70)
        left_paths = []
        seen_paths = set()
        for entry in reversed(left_history):
            path = entry['path']
            if path not in seen_paths:
                left_paths.append(path)
                seen_paths.add(path)
        
        for i, path in enumerate(left_paths):
            print(f"  {i+1}. {Path(path).name}")
        
        print(f"\n🔍 Left pane shows {len(left_paths)} unique directories")
        print("   (Most recent: backend, config, frontend, docs, tests)")
        print()
        
        # Show right pane history
        print("📋 History - Right")
        print("💡 Help: ↑↓:select  Enter:choose  TAB:switch to Left  Type:search  ESC:cancel")
        print("=" * 70)
        right_paths = []
        seen_paths = set()
        for entry in reversed(right_history):
            path = entry['path']
            if path not in seen_paths:
                right_paths.append(path)
                seen_paths.add(path)
        
        for i, path in enumerate(right_paths):
            print(f"  {i+1}. {Path(path).name}")
        
        print(f"\n🔍 Right pane shows {len(right_paths)} unique directories")
        print("   (Most recent: frontend, backend, tests, docs, config)")
        print()
        
        # Demonstrate the TAB switching workflow
        print("--- TAB Switching Workflow ---")
        print("🎯 User Scenario: Developer wants to navigate between project areas")
        print()
        
        print("1️⃣ Developer presses 'H' while left pane is active:")
        print("   📋 Shows: History - Left")
        print("   💡 Help: ↑↓:select  Enter:choose  TAB:switch to Right  Type:search  ESC:cancel")
        print("   📂 Displays: backend, config, frontend, docs, tests")
        print()
        
        print("2️⃣ Developer presses TAB to see right pane history:")
        print("   📋 Shows: History - Right")
        print("   💡 Help: ↑↓:select  Enter:choose  TAB:switch to Left  Type:search  ESC:cancel")
        print("   📂 Displays: frontend, backend, tests, docs, config")
        print()
        
        print("3️⃣ Developer presses TAB again to return to left pane history:")
        print("   📋 Shows: History - Left")
        print("   💡 Help: ↑↓:select  Enter:choose  TAB:switch to Right  Type:search  ESC:cancel")
        print("   📂 Back to: backend, config, frontend, docs, tests")
        print()
        
        print("4️⃣ Developer can select any directory from either pane's history:")
        print("   ✅ Navigate current pane to selected directory")
        print("   ✅ Cursor position restored to previous file")
        print("   ✅ Instant access to any previously visited location")
        print()
        
        # Show the benefits
        print("=== Benefits of TAB Switching ===")
        print("🚀 Enhanced Navigation:")
        print("   • Access BOTH pane histories from one dialog")
        print("   • Switch between left/right histories with TAB")
        print("   • Use right pane history for left pane navigation (and vice versa)")
        print("   • No need to switch panes to access their histories")
        print()
        
        print("💡 Use Cases:")
        print("   • Compare directory structures between panes")
        print("   • Navigate left pane using right pane's history")
        print("   • Quick access to directories visited in either pane")
        print("   • Cross-pane workflow navigation")
        print()
        
        print("⌨️  Keyboard Shortcuts:")
        print("   • H key: Show cursor history dialog")
        print("   • TAB key: Switch between left/right pane histories")
        print("   • Enter: Navigate to selected directory")
        print("   • ESC: Cancel dialog")
        print("   • Type: Search/filter directories")
        print()
        
        # Demonstrate cross-pane navigation benefit
        print("--- Cross-Pane Navigation Example ---")
        print("🎯 Scenario: Left pane needs to access right pane's visited directories")
        print()
        
        print("Current situation:")
        print(f"   📂 Left pane: {Path(left_paths[0]).name} (most recent)")
        print(f"   📂 Right pane: {Path(right_paths[0]).name} (most recent)")
        print()
        
        print("With TAB switching:")
        print("   1. Press 'H' in left pane → See left history")
        print("   2. Press TAB → See right history")  
        print("   3. Select 'docs' from right history")
        print("   4. Left pane navigates to docs/ (from right pane's history)")
        print("   ✅ Cross-pane navigation achieved!")
        print()
        
        # Show technical implementation
        print("--- Technical Implementation ---")
        print("🔧 Enhanced ListDialog:")
        print("   • Added custom_key_handler parameter")
        print("   • TAB key (keycode 9) triggers pane switching")
        print("   • Dialog title shows current pane and TAB hint")
        print()
        
        print("🔧 Cursor History Dialog:")
        print("   • _show_cursor_history_for_pane() method")
        print("   • Custom TAB handler switches between panes")
        print("   • Maintains separate histories for left/right")
        print("   • Seamless switching without losing context")
        print()
        
        # Clean up
        state_manager.cleanup_session()
        print("✅ TAB switching demonstration completed!")
        print()
        
        print("=== Summary ===")
        print("The enhanced cursor history dialog now supports:")
        print("✅ TAB key switching between left and right pane histories")
        print("✅ Cross-pane navigation (use right history for left pane)")
        print("✅ Clear visual indication of current pane and switching option")
        print("✅ Seamless workflow without losing search context")
        print("✅ Enhanced productivity for complex directory navigation")


if __name__ == "__main__":
    demo_cursor_history_tab_switching()