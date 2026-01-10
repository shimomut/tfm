# SearchDialog Per-Thread Cancel Event Fix

## Problem

When searching SFTP directories, typing rapidly (e.g., "boto3") would trigger multiple concurrent searches that couldn't be properly cancelled. Old search threads would continue running even after being "cancelled", causing results to overwrite each other.

## Root Cause

All search threads shared a single `self.cancel_search` event. When starting a new search:

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

## Solution

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
    # Use the cancel_event passed to THIS thread
    for file_path in search_root.rglob('*'):
        if cancel_event.is_set():  # Check THIS thread's event
            return
        # ... process file
```

## Changes

**Modified Files:**
- `src/tfm_search_dialog.py`
  - Changed `self.cancel_search` (shared) to `self.current_cancel_event` (per-thread)
  - Modified `perform_search()` to create a new cancel event for each thread
  - Updated `_search_worker()` to accept `cancel_event` parameter
  - Modified `_cancel_current_search()` to use the current thread's cancel event

**New Files:**
- `test/test_search_per_thread_cancel.py` - Tests for per-thread cancel events

## Testing

```bash
PYTHONPATH=.:src:ttk python3 test/test_search_per_thread_cancel.py
# 2 tests pass
```

## Result

- Each search thread has its own cancel event that persists for the thread's lifetime
- Old threads can be cancelled even if they don't finish within 0.1s
- No race conditions or result conflicts
- Searches cancel immediately and independently
