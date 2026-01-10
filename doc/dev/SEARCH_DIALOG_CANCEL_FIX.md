# SearchDialog SearchThread Class Refactoring

## Problem
When searching SFTP directories, typing rapidly (e.g., "boto3") would trigger multiple concurrent searches that couldn't be properly cancelled. Old search threads would continue running even after being "cancelled", causing results to overwrite each other.

## Root Causes

### 1. Shared Cancel Event
All search threads shared a single `self.cancel_search` event. When starting a new search:
1. Set `cancel_search.set()` to signal cancellation
2. Wait 0.1s with `join(timeout=0.1)` 
3. Clear `cancel_search.clear()` for next search

For slow SFTP operations (2-5 seconds), 0.1s wasn't enough. Old threads continued running with a **cleared** cancel event, making them uninterruptible.

### 2. Shared Searching Flag
Similarly, `self.searching` was a shared flag that could be overwritten by old threads. When a new search started, it would set `self.searching = True`, but an old thread finishing later would set it to `False`, even though the new search was still running.

## Solution: SearchThread Class

Created a dedicated `SearchThread` class that encapsulates per-thread state:

```python
class SearchThread(threading.Thread):
    """Dedicated thread class for search operations with built-in cancellation support"""
    
    def __init__(self, search_root, pattern_text, search_type, worker_func, *args, **kwargs):
        super().__init__(daemon=True, *args, **kwargs)
        self.search_root = search_root
        self.pattern_text = pattern_text
        self.search_type = search_type
        self.worker_func = worker_func
        self.cancel_event = threading.Event()  # Per-thread cancel event
        self.searching = True  # Per-thread searching flag
        
    def run(self):
        """Execute the search worker function"""
        try:
            self.worker_func(self.search_root, self.pattern_text, self.search_type, self)
        finally:
            self.searching = False  # Thread sets its own flag
    
    def cancel(self):
        """Request cancellation of this search thread"""
        self.cancel_event.set()
    
    def is_cancelled(self):
        """Check if cancellation has been requested"""
        return self.cancel_event.is_set()
```

### Benefits

1. **Encapsulation**: Each thread owns its `cancel_event` and `searching` flag
2. **No Race Conditions**: Old threads can't overwrite shared state
3. **Cleaner Code**: Thread state is self-contained and obvious
4. **Better OOP**: Follows object-oriented principles

### Usage

```python
# Create new SearchThread
self.search_thread = SearchThread(
    search_root, pattern_text, self.search_type, self._search_worker
)
self.search_thread.start()

# Cancel current search
if self.search_thread and self.search_thread.is_alive():
    self.search_thread.cancel()
    self.search_thread.join(timeout=0.1)

# Check if searching
is_searching = self.search_thread and self.search_thread.is_alive() and self.search_thread.searching

# Worker checks cancellation
def _search_worker(self, search_root, pattern_text, search_type, search_thread):
    for file_path in search_root.rglob('*'):
        if search_thread.is_cancelled():
            return
        # ... process file
```

## Changes

**Modified Files:**
- `src/tfm_search_dialog.py`
  - Added `SearchThread` class with per-thread `cancel_event` and `searching` properties
  - Removed `self.cancel_search` and `self.current_cancel_event` from SearchDialog
  - Removed `self.searching` from SearchDialog
  - Modified `perform_search()` to create SearchThread instances
  - Updated `_cancel_current_search()` to use `search_thread.cancel()`
  - Updated `_search_worker()` to accept `search_thread` parameter
  - Updated all cancellation checks to use `search_thread.is_cancelled()`
  - Updated all searching checks to use `search_thread.searching`

**Updated Files:**
- `test/test_search_per_thread_cancel.py` - Updated to test SearchThread instances
- `test/test_search_searching_flag_race.py` - Updated to test SearchThread.searching property

## Testing

```bash
# Test per-thread cancel events
PYTHONPATH=.:src:ttk python -m pytest test/test_search_per_thread_cancel.py -v
# 2 tests pass

# Test searching flag race condition
PYTHONPATH=.:src:ttk python -m pytest test/test_search_searching_flag_race.py -v
# 3 tests pass

# Run all search tests together
PYTHONPATH=.:src:ttk python -m pytest test/test_search_per_thread_cancel.py test/test_search_searching_flag_race.py -v
# 5 tests pass
```

## Result

- Each search has its own SearchThread instance with dedicated state
- Old threads can be cancelled even if they don't finish within 0.1s
- Old threads cannot overwrite searching flag when new search is running
- No race conditions or result conflicts
- Searches cancel immediately and independently
- Cleaner, more maintainable object-oriented design

```python
# Old implementation (BROKEN)
def _cancel_current_search(self):
    self.cancel_search.set()      # Signal cancellation
    thread.join(timeout=0.1)      # Wait 0.1s for thread to finish
    # Problem: For slow SFTP, 0.1s isn't enough!

def perform_search(self, search_root):
    self._cancel_current_search()  # Try to cancel old thread
    self.cancel_search.clear()     # Clear the event for new search
    # Problem: Old thread still running but event is now cleared!
    
    self.search_thread = threading.Thread(
        target=self._search_worker,
        args=(search_root, pattern, search_type),  # Uses self.cancel_search
        daemon=True
    )
    self.search_thread.start()
```

**The Race Condition**: For SFTP operations that take 2-5 seconds, the 0.1s timeout wasn't enough. The old thread would continue running but with a **cleared** cancel event, making it uninterruptible.

### 2. Shared Searching Flag

Similarly, `self.searching` was a shared flag that could be overwritten by old threads:

```python
# Old implementation (BROKEN)
def _search_worker(self, ...):
    # ... do search work
    
    # Problem: Old thread can overwrite this even when new search is running!
    self.searching = False
```

**The Race Condition**: When a new search started, it would set `self.searching = True`. But an old thread finishing later would set it to `False`, even though the new search was still running.

## Solution

### 1. Per-Thread Cancel Events

Each search thread now gets its own dedicated cancel event:

```python
# New implementation (CORRECT)
def perform_search(self, search_root):
    self._cancel_current_search()  # Cancel old thread with its own event
    
    # Create NEW cancel event for THIS thread
    cancel_event = threading.Event()
    self.current_cancel_event = cancel_event
    
    self.search_thread = threading.Thread(
        target=self._search_worker,
        args=(search_root, pattern, search_type, cancel_event),  # Pass event
        daemon=True
    )
    self.search_thread.start()

def _cancel_current_search(self):
    if self.search_thread and self.search_thread.is_alive():
        # Signal THIS thread's cancel event
        if self.current_cancel_event:
            self.current_cancel_event.set()
        # Wait briefly (old thread keeps its cancel event)
        self.search_thread.join(timeout=0.1)
    
    # Clear references (but old thread still has its cancel event)
    self.search_thread = None
    self.current_cancel_event = None

def _search_worker(self, search_root, pattern_text, search_type, cancel_event):
    # Check if this thread is still current
    def is_current_thread():
        return self.current_cancel_event is cancel_event
    
    # Use the cancel_event passed to THIS thread
    for file_path in search_root.rglob('*'):
        if cancel_event.is_set():  # Check THIS thread's event
            # Only update searching flag if this is still the current thread
            with self.search_lock:
                if is_current_thread():
                    self.searching = False
            return
        # ... process file
```

### 2. Thread-Aware Searching Flag

Only the current thread can set `self.searching = False`:

```python
def _search_worker(self, search_root, pattern_text, search_type, cancel_event):
    # Define helper to check if this is still the current thread
    def is_current_thread():
        return self.current_cancel_event is cancel_event
    
    try:
        # ... do search work
        
        # Check for cancellation
        if cancel_event.is_set():
            with self.search_lock:
                # Only update if this is still the current thread
                if is_current_thread():
                    self.searching = False
            return
        
        # ... more search work
    finally:
        # Final update - only if this is still the current thread
        if not cancel_event.is_set():
            with self.search_lock:
                if is_current_thread():
                    self.searching = False
```

## Changes

**Modified Files:**
- `src/tfm_search_dialog.py`
  - Changed `self.cancel_search` (shared) to `self.current_cancel_event` (per-thread)
  - Modified `perform_search()` to create a new cancel event for each thread
  - Updated `_search_worker()` to accept `cancel_event` parameter
  - Modified `_cancel_current_search()` to use the current thread's cancel event
  - Added `is_current_thread()` check before setting `self.searching = False`

**New Files:**
- `test/test_search_per_thread_cancel.py` - Tests for per-thread cancel events
- `test/test_search_searching_flag_race.py` - Tests for searching flag race condition

## Testing

```bash
# Test per-thread cancel events
PYTHONPATH=.:src:ttk python -m pytest test/test_search_per_thread_cancel.py -v
# 2 tests pass

# Test searching flag race condition
PYTHONPATH=.:src:ttk python -m pytest test/test_search_searching_flag_race.py -v
# 3 tests pass
```

## Result

- Each search thread has its own cancel event that persists for the thread's lifetime
- Old threads can be cancelled even if they don't finish within 0.1s
- Old threads cannot overwrite `self.searching` flag when new search is running
- No race conditions or result conflicts
- Searches cancel immediately and independently
