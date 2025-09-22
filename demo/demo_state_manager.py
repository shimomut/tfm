#!/usr/bin/env python3
"""
TFM State Manager Demo

Demonstrates the persistent state management system functionality.
This script shows how TFM saves and restores application state.
"""

import sys
import time
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tfm_state_manager import TFMStateManager


def demo_basic_operations():
    """Demonstrate basic state operations."""
    print("=== Basic State Operations Demo ===")
    
    # Create state manager
    state_manager = TFMStateManager("demo_instance")
    
    # Save some application preferences
    print("Saving application preferences...")
    state_manager.set_state("color_scheme", "dark")
    state_manager.set_state("show_hidden_files", True)
    state_manager.set_state("default_sort", "name")
    
    # Save complex data
    user_settings = {
        "editor": "vim",
        "terminal": "zsh",
        "favorite_paths": ["/home/user", "/tmp", "/var/log"],
        "window_size": {"width": 120, "height": 40}
    }
    state_manager.set_state("user_settings", user_settings)
    
    # Load and display saved data
    print("\nLoading saved preferences:")
    print(f"Color scheme: {state_manager.get_state('color_scheme')}")
    print(f"Show hidden files: {state_manager.get_state('show_hidden_files')}")
    print(f"Default sort: {state_manager.get_state('default_sort')}")
    
    loaded_settings = state_manager.get_state("user_settings")
    print(f"Editor: {loaded_settings['editor']}")
    print(f"Terminal: {loaded_settings['terminal']}")
    print(f"Favorite paths: {loaded_settings['favorite_paths']}")
    
    # Demonstrate default values
    print(f"Non-existent setting: {state_manager.get_state('missing_key', 'default_value')}")
    
    state_manager.cleanup_session()
    print("✓ Basic operations completed\n")


def demo_pane_state():
    """Demonstrate pane state management."""
    print("=== Pane State Management Demo ===")
    
    state_manager = TFMStateManager("demo_panes")
    
    # Simulate left pane state
    left_pane = {
        'path': '/home/user/projects',
        'selected_index': 3,
        'scroll_offset': 1,
        'sort_mode': 'size',
        'sort_reverse': True,
        'filter_pattern': '*.py',
        'selected_files': ['/home/user/projects/main.py', '/home/user/projects/utils.py']
    }
    
    # Simulate right pane state
    right_pane = {
        'path': '/tmp',
        'selected_index': 0,
        'scroll_offset': 0,
        'sort_mode': 'date',
        'sort_reverse': False,
        'filter_pattern': '',
        'selected_files': []
    }
    
    print("Saving pane states...")
    state_manager.save_pane_state('left', left_pane)
    state_manager.save_pane_state('right', right_pane)
    
    print("Loading pane states...")
    loaded_left = state_manager.load_pane_state('left')
    loaded_right = state_manager.load_pane_state('right')
    
    print(f"Left pane - Path: {loaded_left['path']}")
    print(f"Left pane - Selected: {loaded_left['selected_index']}")
    print(f"Left pane - Sort: {loaded_left['sort_mode']} ({'desc' if loaded_left['sort_reverse'] else 'asc'})")
    print(f"Left pane - Filter: '{loaded_left['filter_pattern']}'")
    print(f"Left pane - Selected files: {len(loaded_left['selected_files'])}")
    
    print(f"Right pane - Path: {loaded_right['path']}")
    print(f"Right pane - Sort: {loaded_right['sort_mode']} ({'desc' if loaded_right['sort_reverse'] else 'asc'})")
    
    state_manager.cleanup_session()
    print("✓ Pane state management completed\n")


def demo_window_layout():
    """Demonstrate window layout persistence."""
    print("=== Window Layout Demo ===")
    
    state_manager = TFMStateManager("demo_layout")
    
    # Save window layout
    print("Saving window layout (70% left pane, 20% log)...")
    state_manager.save_window_layout(0.7, 0.2)
    
    # Load window layout
    layout = state_manager.load_window_layout()
    print(f"Loaded layout - Left pane: {int(layout['left_pane_ratio']*100)}%")
    print(f"Loaded layout - Right pane: {int((1-layout['left_pane_ratio'])*100)}%")
    print(f"Loaded layout - Log pane: {int(layout['log_height_ratio']*100)}%")
    
    state_manager.cleanup_session()
    print("✓ Window layout demo completed\n")


def demo_recent_directories():
    """Demonstrate recent directories management."""
    print("=== Recent Directories Demo ===")
    
    state_manager = TFMStateManager("demo_recent")
    
    # Add some recent directories
    directories = [
        '/home/user/documents',
        '/home/user/downloads',
        '/home/user/projects/python',
        '/var/log',
        '/tmp',
        '/home/user/desktop'
    ]
    
    print("Adding recent directories...")
    for directory in directories:
        state_manager.add_recent_directory(directory)
        print(f"  Added: {directory}")
    
    # Load recent directories
    recent = state_manager.load_recent_directories()
    print(f"\nRecent directories (most recent first):")
    for i, directory in enumerate(recent[:5], 1):
        print(f"  {i}. {directory}")
    
    # Add a duplicate (should move to front)
    print(f"\nAdding duplicate directory: {directories[0]}")
    state_manager.add_recent_directory(directories[0])
    
    recent = state_manager.load_recent_directories()
    print(f"Most recent directory is now: {recent[0]}")
    
    state_manager.cleanup_session()
    print("✓ Recent directories demo completed\n")


def demo_search_history():
    """Demonstrate search history management."""
    print("=== Search History Demo ===")
    
    state_manager = TFMStateManager("demo_search")
    
    # Add search terms
    search_terms = [
        '*.py',
        'TODO',
        'function main',
        '*.log',
        'error',
        'class.*Test'
    ]
    
    print("Adding search terms...")
    for term in search_terms:
        state_manager.add_search_term(term)
        print(f"  Added: '{term}'")
    
    # Load search history
    history = state_manager.load_search_history()
    print(f"\nSearch history (most recent first):")
    for i, term in enumerate(history[:5], 1):
        print(f"  {i}. '{term}'")
    
    # Add a duplicate (should move to front)
    print(f"\nSearching again for: '{search_terms[1]}'")
    state_manager.add_search_term(search_terms[1])
    
    history = state_manager.load_search_history()
    print(f"Most recent search is now: '{history[0]}'")
    
    state_manager.cleanup_session()
    print("✓ Search history demo completed\n")


def demo_session_management():
    """Demonstrate session management."""
    print("=== Session Management Demo ===")
    
    # Create multiple sessions
    session1 = TFMStateManager("demo_session_1")
    session2 = TFMStateManager("demo_session_2")
    
    print("Created two demo sessions")
    
    # Check active sessions
    sessions = session1.get_active_sessions()
    print(f"Active sessions: {len(sessions)}")
    
    for session in sessions:
        if session['instance_id'].startswith('demo_session'):
            print(f"  Session: {session['instance_id']}")
            print(f"    PID: {session['pid']}")
            print(f"    Host: {session['hostname']}")
            print(f"    Started: {time.ctime(session['started_at'])}")
    
    # Update heartbeat
    print("\nUpdating session heartbeats...")
    session1.update_session_heartbeat()
    session2.update_session_heartbeat()
    
    # Cleanup sessions
    print("Cleaning up sessions...")
    session1.cleanup_session()
    session2.cleanup_session()
    
    # Check sessions after cleanup
    remaining_sessions = session1.get_active_sessions()
    demo_sessions = [s for s in remaining_sessions if s['instance_id'].startswith('demo_session')]
    print(f"Demo sessions remaining after cleanup: {len(demo_sessions)}")
    
    print("✓ Session management demo completed\n")


def demo_multi_instance_safety():
    """Demonstrate multi-instance safety."""
    print("=== Multi-Instance Safety Demo ===")
    
    import threading
    import random
    
    results = []
    errors = []
    
    def worker_instance(instance_id, operations=10):
        """Simulate a TFM instance performing operations."""
        try:
            state_manager = TFMStateManager(f"worker_{instance_id}")
            
            for i in range(operations):
                # Perform various operations
                key = f"worker_{instance_id}_data_{i}"
                value = {
                    'operation': i,
                    'timestamp': time.time(),
                    'random_data': random.randint(1, 1000)
                }
                
                if state_manager.set_state(key, value):
                    loaded = state_manager.get_state(key)
                    if loaded and loaded['operation'] == i:
                        results.append(f"Worker {instance_id}: Operation {i} successful")
                    else:
                        errors.append(f"Worker {instance_id}: Data mismatch in operation {i}")
                else:
                    errors.append(f"Worker {instance_id}: Failed to save operation {i}")
                
                # Small delay to increase concurrency
                time.sleep(0.01)
            
            state_manager.cleanup_session()
            
        except Exception as e:
            errors.append(f"Worker {instance_id}: Exception {e}")
    
    print("Starting 3 concurrent worker instances...")
    
    # Start worker threads
    threads = []
    for i in range(3):
        thread = threading.Thread(target=worker_instance, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for completion
    for thread in threads:
        thread.join()
    
    print(f"Operations completed: {len(results)}")
    print(f"Errors encountered: {len(errors)}")
    
    if errors:
        print("Sample errors:")
        for error in errors[:3]:
            print(f"  {error}")
    else:
        print("✓ All operations completed successfully!")
    
    print("✓ Multi-instance safety demo completed\n")


def demo_persistence():
    """Demonstrate state persistence across instances."""
    print("=== State Persistence Demo ===")
    
    # Create first instance and save data
    print("Creating first instance and saving data...")
    instance1 = TFMStateManager("persistence_test_1")
    
    test_data = {
        'application': 'TFM',
        'version': '1.0',
        'settings': {
            'theme': 'dark',
            'language': 'en',
            'auto_save': True
        },
        'timestamp': time.time()
    }
    
    instance1.set_state("persistent_data", test_data)
    instance1.save_window_layout(0.6, 0.3)
    instance1.add_recent_directory("/persistent/path/1")
    instance1.add_recent_directory("/persistent/path/2")
    
    print("  Saved application data")
    print("  Saved window layout")
    print("  Added recent directories")
    
    # Clean up first instance
    instance1.cleanup_session()
    print("  Cleaned up first instance")
    
    # Create second instance and load data
    print("\nCreating second instance and loading data...")
    instance2 = TFMStateManager("persistence_test_2")
    
    loaded_data = instance2.get_state("persistent_data")
    loaded_layout = instance2.load_window_layout()
    loaded_recent = instance2.load_recent_directories()
    
    print(f"  Loaded application: {loaded_data['application']}")
    print(f"  Loaded theme: {loaded_data['settings']['theme']}")
    print(f"  Loaded layout: {int(loaded_layout['left_pane_ratio']*100)}% | {int(loaded_layout['log_height_ratio']*100)}%")
    print(f"  Loaded recent directories: {len(loaded_recent)} entries")
    print(f"    Most recent: {loaded_recent[0] if loaded_recent else 'None'}")
    
    # Verify data integrity
    if (loaded_data['application'] == test_data['application'] and
        loaded_data['settings']['theme'] == test_data['settings']['theme'] and
        loaded_layout['left_pane_ratio'] == 0.6 and
        "/persistent/path/2" in loaded_recent):
        print("✓ Data persistence verified!")
    else:
        print("✗ Data persistence failed!")
    
    instance2.cleanup_session()
    print("✓ State persistence demo completed\n")


def main():
    """Run all demonstrations."""
    print("TFM State Manager Demonstration")
    print("=" * 50)
    print()
    
    try:
        demo_basic_operations()
        demo_pane_state()
        demo_window_layout()
        demo_recent_directories()
        demo_search_history()
        demo_session_management()
        demo_multi_instance_safety()
        demo_persistence()
        
        print("=" * 50)
        print("All demonstrations completed successfully!")
        print()
        print("The state database is located at: ~/.tfm/state.db")
        print("You can inspect it with any SQLite browser or command-line tool.")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)