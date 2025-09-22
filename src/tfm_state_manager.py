#!/usr/bin/env python3
"""
TFM State Manager - Persistent Application State Management

Manages persistent application state using SQLite database.
Handles multiple TFM instances safely with proper locking and error handling.
"""

import sqlite3
import json
import time
import threading
from pathlib import Path
from contextlib import contextmanager
from typing import Any, Dict, Optional, List


class StateManager:
    """
    Manages persistent application state using SQLite database.
    
    Features:
    - Thread-safe operations with proper locking
    - Multiple instance support with retry logic
    - Automatic database creation and migration
    - JSON serialization for complex data types
    - Graceful error handling and fallback behavior
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the state manager.
        
        Args:
            db_path: Optional custom database path. Defaults to ~/.tfm/state.db
        """
        if db_path is None:
            self.db_path = Path.home() / '.tfm' / 'state.db'
        else:
            self.db_path = Path(db_path)
        
        # Ensure the directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Thread lock for database operations
        self._lock = threading.RLock()
        
        # Connection settings for better concurrency
        self._connection_timeout = 30.0  # 30 seconds
        self._retry_attempts = 3
        self._retry_delay = 0.1  # 100ms
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the database with required tables."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Create state table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS app_state (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at REAL NOT NULL,
                        instance_id TEXT
                    )
                ''')
                
                # Create session table for tracking active instances
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sessions (
                        instance_id TEXT PRIMARY KEY,
                        pid INTEGER NOT NULL,
                        started_at REAL NOT NULL,
                        last_seen REAL NOT NULL,
                        hostname TEXT
                    )
                ''')
                
                # Create index for better performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_state_updated 
                    ON app_state(updated_at)
                ''')
                
                conn.commit()
                
        except Exception as e:
            print(f"Warning: Could not initialize state database: {e}")
    
    @contextmanager
    def _get_connection(self):
        """
        Get a database connection with proper error handling and retry logic.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        for attempt in range(self._retry_attempts):
            try:
                conn = sqlite3.connect(
                    str(self.db_path),
                    timeout=self._connection_timeout,
                    isolation_level=None  # Autocommit mode
                )
                
                # Enable WAL mode for better concurrency
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA synchronous=NORMAL')
                conn.execute('PRAGMA temp_store=MEMORY')
                conn.execute('PRAGMA mmap_size=268435456')  # 256MB
                
                yield conn
                return
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and attempt < self._retry_attempts - 1:
                    time.sleep(self._retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    raise
            except Exception as e:
                raise
            finally:
                if conn:
                    conn.close()
    
    def _serialize_value(self, value: Any) -> str:
        """
        Serialize a value to JSON string.
        
        Args:
            value: Value to serialize
            
        Returns:
            str: JSON string representation
        """
        try:
            # First try with default=str
            return json.dumps(value, default=str, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            # If that fails, try without default (will fail for non-serializable types)
            try:
                return json.dumps(value, ensure_ascii=False)
            except (TypeError, ValueError):
                raise ValueError(f"Cannot serialize value: {e}")
    
    def _deserialize_value(self, json_str: str) -> Any:
        """
        Deserialize a JSON string to Python value.
        
        Args:
            json_str: JSON string to deserialize
            
        Returns:
            Any: Deserialized Python value
        """
        try:
            return json.loads(json_str)
        except Exception as e:
            raise ValueError(f"Cannot deserialize value: {e}")
    
    def set_state(self, key: str, value: Any, instance_id: Optional[str] = None) -> bool:
        """
        Set a state value.
        
        Args:
            key: State key
            value: State value (will be JSON serialized)
            instance_id: Optional instance identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self._lock:
            try:
                serialized_value = self._serialize_value(value)
                current_time = time.time()
                
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO app_state 
                        (key, value, updated_at, instance_id)
                        VALUES (?, ?, ?, ?)
                    ''', (key, serialized_value, current_time, instance_id))
                
                return True
                
            except Exception as e:
                print(f"Warning: Could not set state '{key}': {e}")
                return False
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get a state value.
        
        Args:
            key: State key
            default: Default value if key not found
            
        Returns:
            Any: State value or default
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT value FROM app_state WHERE key = ?
                    ''', (key,))
                    
                    row = cursor.fetchone()
                    if row:
                        return self._deserialize_value(row[0])
                    else:
                        return default
                        
            except Exception as e:
                print(f"Warning: Could not get state '{key}': {e}")
                return default
    
    def delete_state(self, key: str) -> bool:
        """
        Delete a state value.
        
        Args:
            key: State key to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM app_state WHERE key = ?', (key,))
                
                return True
                
            except Exception as e:
                print(f"Warning: Could not delete state '{key}': {e}")
                return False
    
    def get_all_states(self, prefix: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all state values, optionally filtered by key prefix.
        
        Args:
            prefix: Optional key prefix filter
            
        Returns:
            Dict[str, Any]: Dictionary of all matching state values
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    if prefix:
                        cursor.execute('''
                            SELECT key, value FROM app_state 
                            WHERE key LIKE ? 
                            ORDER BY key
                        ''', (f"{prefix}%",))
                    else:
                        cursor.execute('''
                            SELECT key, value FROM app_state 
                            ORDER BY key
                        ''')
                    
                    result = {}
                    for key, value in cursor.fetchall():
                        try:
                            result[key] = self._deserialize_value(value)
                        except Exception as e:
                            print(f"Warning: Could not deserialize state '{key}': {e}")
                    
                    return result
                    
            except Exception as e:
                print(f"Warning: Could not get all states: {e}")
                return {}
    
    def clear_all_states(self, prefix: Optional[str] = None) -> bool:
        """
        Clear all state values, optionally filtered by key prefix.
        
        Args:
            prefix: Optional key prefix filter
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    if prefix:
                        cursor.execute('DELETE FROM app_state WHERE key LIKE ?', (f"{prefix}%",))
                    else:
                        cursor.execute('DELETE FROM app_state')
                
                return True
                
            except Exception as e:
                print(f"Warning: Could not clear states: {e}")
                return False


class TFMStateManager(StateManager):
    """
    TFM-specific state manager with convenience methods for common state operations.
    """
    
    def __init__(self, instance_id: Optional[str] = None):
        """
        Initialize TFM state manager.
        
        Args:
            instance_id: Optional instance identifier for this TFM session
        """
        super().__init__()
        
        # Generate instance ID if not provided
        if instance_id is None:
            import os
            import socket
            self.instance_id = f"tfm_{os.getpid()}_{socket.gethostname()}_{int(time.time())}"
        else:
            self.instance_id = instance_id
        
        # Register this session
        self._register_session()
    
    def _register_session(self):
        """Register this TFM session in the sessions table."""
        try:
            import os
            import socket
            
            current_time = time.time()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO sessions 
                    (instance_id, pid, started_at, last_seen, hostname)
                    VALUES (?, ?, ?, ?, ?)
                ''', (self.instance_id, os.getpid(), current_time, current_time, socket.gethostname()))
                
        except Exception as e:
            print(f"Warning: Could not register session: {e}")
    
    def update_session_heartbeat(self):
        """Update the last_seen timestamp for this session."""
        try:
            current_time = time.time()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE sessions SET last_seen = ? WHERE instance_id = ?
                ''', (current_time, self.instance_id))
                
        except Exception as e:
            print(f"Warning: Could not update session heartbeat: {e}")
    
    def cleanup_session(self):
        """Clean up this session from the sessions table."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM sessions WHERE instance_id = ?', (self.instance_id,))
                
        except Exception as e:
            print(f"Warning: Could not cleanup session: {e}")
    
    def get_active_sessions(self, timeout_seconds: float = 300.0) -> List[Dict[str, Any]]:
        """
        Get list of active TFM sessions.
        
        Args:
            timeout_seconds: Session timeout in seconds (default 5 minutes)
            
        Returns:
            List[Dict[str, Any]]: List of active session information
        """
        try:
            current_time = time.time()
            cutoff_time = current_time - timeout_seconds
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT instance_id, pid, started_at, last_seen, hostname
                    FROM sessions 
                    WHERE last_seen > ?
                    ORDER BY last_seen DESC
                ''', (cutoff_time,))
                
                sessions = []
                for row in cursor.fetchall():
                    sessions.append({
                        'instance_id': row[0],
                        'pid': row[1],
                        'started_at': row[2],
                        'last_seen': row[3],
                        'hostname': row[4]
                    })
                
                return sessions
                
        except Exception as e:
            print(f"Warning: Could not get active sessions: {e}")
            return []
    
    def cleanup_stale_sessions(self, timeout_seconds: float = 300.0):
        """
        Clean up stale sessions from the database.
        
        Args:
            timeout_seconds: Session timeout in seconds (default 5 minutes)
        """
        try:
            current_time = time.time()
            cutoff_time = current_time - timeout_seconds
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM sessions WHERE last_seen <= ?', (cutoff_time,))
                
        except Exception as e:
            print(f"Warning: Could not cleanup stale sessions: {e}")
    
    # TFM-specific convenience methods
    
    def save_pane_state(self, pane_name: str, pane_data: Dict[str, Any]) -> bool:
        """
        Save pane state (directory, selection, scroll position, etc.).
        
        Args:
            pane_name: Name of the pane ('left' or 'right')
            pane_data: Pane data dictionary
            
        Returns:
            bool: True if successful
        """
        # Extract serializable state
        state = {
            'path': str(pane_data.get('path', '')),
            'selected_index': pane_data.get('selected_index', 0),
            'scroll_offset': pane_data.get('scroll_offset', 0),
            'sort_mode': pane_data.get('sort_mode', 'name'),
            'sort_reverse': pane_data.get('sort_reverse', False),
            'filter_pattern': pane_data.get('filter_pattern', ''),
            'selected_files': list(pane_data.get('selected_files', set()))
        }
        
        return self.set_state(f"pane.{pane_name}", state, self.instance_id)
    
    def load_pane_state(self, pane_name: str) -> Optional[Dict[str, Any]]:
        """
        Load pane state.
        
        Args:
            pane_name: Name of the pane ('left' or 'right')
            
        Returns:
            Optional[Dict[str, Any]]: Pane state or None if not found
        """
        return self.get_state(f"pane.{pane_name}")
    
    def save_window_layout(self, left_pane_ratio: float, log_height_ratio: float) -> bool:
        """
        Save window layout settings.
        
        Args:
            left_pane_ratio: Left pane width ratio
            log_height_ratio: Log pane height ratio
            
        Returns:
            bool: True if successful
        """
        layout = {
            'left_pane_ratio': left_pane_ratio,
            'log_height_ratio': log_height_ratio
        }
        
        return self.set_state("window.layout", layout, self.instance_id)
    
    def load_window_layout(self) -> Optional[Dict[str, float]]:
        """
        Load window layout settings.
        
        Returns:
            Optional[Dict[str, float]]: Layout settings or None if not found
        """
        return self.get_state("window.layout")
    
    def save_recent_directories(self, directories: List[str], max_count: int = 50) -> bool:
        """
        Save recent directories list.
        
        Args:
            directories: List of recent directory paths
            max_count: Maximum number of directories to keep
            
        Returns:
            bool: True if successful
        """
        # Limit the list size
        recent_dirs = directories[:max_count]
        
        return self.set_state("recent.directories", recent_dirs, self.instance_id)
    
    def load_recent_directories(self) -> List[str]:
        """
        Load recent directories list.
        
        Returns:
            List[str]: List of recent directory paths
        """
        return self.get_state("recent.directories", [])
    
    def add_recent_directory(self, directory: str, max_count: int = 50) -> bool:
        """
        Add a directory to the recent directories list.
        
        Args:
            directory: Directory path to add
            max_count: Maximum number of directories to keep
            
        Returns:
            bool: True if successful
        """
        recent_dirs = self.load_recent_directories()
        
        # Remove if already exists
        if directory in recent_dirs:
            recent_dirs.remove(directory)
        
        # Add to front
        recent_dirs.insert(0, directory)
        
        # Limit size
        recent_dirs = recent_dirs[:max_count]
        
        return self.save_recent_directories(recent_dirs, max_count)
    
    def save_search_history(self, search_terms: List[str], max_count: int = 100) -> bool:
        """
        Save search history.
        
        Args:
            search_terms: List of search terms
            max_count: Maximum number of terms to keep
            
        Returns:
            bool: True if successful
        """
        # Limit the list size
        history = search_terms[:max_count]
        
        return self.set_state("search.history", history, self.instance_id)
    
    def load_search_history(self) -> List[str]:
        """
        Load search history.
        
        Returns:
            List[str]: List of search terms
        """
        return self.get_state("search.history", [])
    
    def add_search_term(self, term: str, max_count: int = 100) -> bool:
        """
        Add a search term to history.
        
        Args:
            term: Search term to add
            max_count: Maximum number of terms to keep
            
        Returns:
            bool: True if successful
        """
        if not term.strip():
            return False
        
        history = self.load_search_history()
        
        # Remove if already exists
        if term in history:
            history.remove(term)
        
        # Add to front
        history.insert(0, term)
        
        # Limit size
        history = history[:max_count]
        
        return self.save_search_history(history, max_count)


# Global state manager instance
_state_manager = None


def get_state_manager() -> TFMStateManager:
    """
    Get the global TFM state manager instance.
    
    Returns:
        TFMStateManager: Global state manager instance
    """
    global _state_manager
    if _state_manager is None:
        _state_manager = TFMStateManager()
    return _state_manager


def cleanup_state_manager():
    """Clean up the global state manager."""
    global _state_manager
    if _state_manager is not None:
        _state_manager.cleanup_session()
        _state_manager = None