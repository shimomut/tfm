# Implementation Plan: Progressive Breadth-First Scanning

## Overview

This implementation plan adds progressive, breadth-first scanning to the Directory Diff Viewer to minimize time-to-first-display and provide a responsive UI during scanning operations. The approach scans only top-level items initially, displays the tree immediately, then progressively scans deeper levels in the background while prioritizing visible items.

## Tasks

- [ ] 1. Add data structures for progressive scanning
  - [ ] 1.1 Add scanning state fields to TreeNode
    ├── Add `children_scanned: bool` field (True if directory contents listed)
    ├── Add `content_compared: bool` field (True if file content compared)
    ├── Add `scan_in_progress: bool` field (True if currently being scanned)
    └── _Requirements: US1, US2, US5_

  - [ ] 1.2 Add PENDING to DifferenceType enum
    ├── Add `PENDING = "pending"` to DifferenceType
    ├── Use for directories/files not yet scanned or compared
    └── _Requirements: US5_

  - [ ] 1.3 Create ScanTask dataclass
    ├── Define fields: left_path, right_path, relative_path, priority, is_visible
    ├── Used for queuing directory scan operations
    └── _Requirements: US2, US4_

  - [ ] 1.4 Create ComparisonTask dataclass
    ├── Define fields: left_path, right_path, relative_path, priority, is_visible
    ├── Used for queuing file comparison operations
    └── _Requirements: US2, US4_

- [ ] 2. Add thread synchronization primitives
  - [ ] 2.1 Add locks for thread safety
    ├── Add `self.data_lock = threading.RLock()` for file dictionaries
    ├── Add `self.tree_lock = threading.RLock()` for tree structure
    ├── Add `self.queue_lock = threading.Lock()` for work queues
    └── _Requirements: US2, US3_

  - [ ] 2.2 Add work queues
    ├── Add `self.scan_queue = queue.Queue()` for directory scanning
    ├── Add `self.priority_queue = queue.PriorityQueue()` for high-priority scans
    ├── Add `self.comparison_queue = queue.Queue()` for file comparisons
    └── _Requirements: US2, US4_

  - [ ] 2.3 Add worker thread management
    ├── Add `self.scanner_thread: Optional[Thread]` field
    ├── Add `self.comparator_thread: Optional[Thread]` field
    ├── Add `self.cancelled: bool` field for shutdown
    └── _Requirements: US2_

- [ ] 3. Implement single-level directory scanning
  - [ ] 3.1 Create _scan_single_level() method
    ├── Scan only immediate children of a directory (non-recursive)
    ├── Return Dict[str, FileInfo] for the scanned level
    ├── Handle permission errors gracefully
    └── _Requirements: US1, US2_

  - [ ] 3.2 Modify start_scan() for top-level only
    ├── Call _scan_single_level() for both root directories
    ├── Build initial tree with PENDING status for subdirectories
    ├── Mark tree as dirty to trigger immediate display
    ├── Start worker threads after initial display
    └── _Requirements: US1_

- [ ] 4. Checkpoint - Verify immediate tree display
  └── Ensure tree displays within 100ms with top-level items visible

- [ ] 5. Implement directory scanner worker thread
  - [ ] 5.1 Create _directory_scanner_worker() method
    ├── Loop: get task from scan_queue
    ├── Call _scan_single_level() for task paths
    ├── Update file dictionaries with thread-safe locking
    ├── Update tree structure to include new children
    ├── Add child directories to scan_queue (breadth-first)
    ├── Mark tree as dirty to trigger UI update
    ├── Check cancelled flag periodically
    └── _Requirements: US2, US3_

  - [ ] 5.2 Create _start_directory_scanner_worker() method
    ├── Create and start scanner thread
    ├── Store thread reference
    └── _Requirements: US2_

  - [ ] 5.3 Implement thread-safe tree updates
    ├── Create _update_tree_node() method
    ├── Use tree_lock for synchronization
    ├── Update node's children_scanned flag
    ├── Add new children to node
    └── _Requirements: US2, US3_

- [ ] 6. Implement file comparator worker thread
  - [ ] 6.1 Create _file_comparator_worker() method
    ├── Loop: get task from comparison_queue
    ├── Call compare_file_content() for task paths
    ├── Update tree node's difference_type
    ├── Update node's content_compared flag
    ├── Mark tree as dirty to trigger UI update
    ├── Check cancelled flag periodically
    └── _Requirements: US2_

  - [ ] 6.2 Create _start_file_comparator_worker() method
    ├── Create and start comparator thread
    ├── Store thread reference
    └── _Requirements: US2_

  - [ ] 6.3 Modify build_tree() to queue file comparisons
    ├── When building tree, don't compare files immediately
    ├── Mark files as PENDING initially
    ├── Add file comparison tasks to comparison_queue
    ├── Prioritize visible files
    └── _Requirements: US2, US4_

- [ ] 7. Checkpoint - Verify background scanning works
  └── Ensure tree updates progressively as directories are scanned

- [ ] 8. Implement priority system
  - [ ] 8.1 Define priority levels
    ├── IMMEDIATE = 1000 (user just expanded)
    ├── VISIBLE = 100 (currently visible)
    ├── EXPANDED = 50 (expanded but scrolled off)
    ├── NORMAL = 10 (not visible, not expanded)
    ├── LOW = 1 (one-sided directories)
    └── _Requirements: US4_

  - [ ] 8.2 Implement _get_visible_nodes_range() method
    ├── Calculate which nodes are currently visible in viewport
    ├── Return list of visible TreeNodes
    └── _Requirements: US4_

  - [ ] 8.3 Implement _update_priorities() method
    ├── Called when viewport changes (scroll, expand, collapse)
    ├── Get visible nodes
    ├── For unscanned visible nodes, add to priority_queue
    └── _Requirements: US4_

  - [ ] 8.4 Create _priority_handler_worker() method
    ├── Loop: get task from priority_queue
    ├── Move task to front of scan_queue
    ├── Check cancelled flag periodically
    └── _Requirements: US4_

  - [ ] 8.5 Call _update_priorities() on scroll and expand/collapse
    ├── Add call in handle_key_event() for UP/DOWN/PgUp/PgDn
    ├── Add call in expand_node() and collapse_node()
    └── _Requirements: US4_

- [ ] 9. Implement on-demand scanning for user expansion
  - [ ] 9.1 Modify expand_node() for immediate scanning
    ├── Check if node.children_scanned is False
    ├── If not scanned, set scan_in_progress = True
    ├── Call _scan_single_level() in main thread
    ├── Update tree with new children
    ├── Set children_scanned = True, scan_in_progress = False
    ├── Mark tree as dirty
    └── _Requirements: US3_

  - [ ] 9.2 Add loading indicator during on-demand scan
    ├── Show "scanning..." text while scan_in_progress is True
    ├── Update status bar with current operation
    └── _Requirements: US3, US5_

- [ ] 10. Implement lazy scanning for one-sided directories
  - [ ] 10.1 Modify _directory_scanner_worker() to skip one-sided dirs
    ├── Check if directory exists in both sides
    ├── If only on one side, don't add to scan_queue automatically
    ├── Mark as PENDING with low priority
    └── _Requirements: US2_

  - [ ] 10.2 Ensure expand_node() handles one-sided directories
    ├── When user expands one-sided directory, scan it immediately
    ├── Update tree with contents
    └── _Requirements: US3_

- [ ] 11. Checkpoint - Verify on-demand and lazy scanning
  └── Ensure expanding unscanned directories works correctly

- [ ] 12. Add visual indicators for pending status
  - [ ] 12.1 Update _get_node_display_text() for pending indicators
    ├── If scan_in_progress, show "[scanning...]"
    ├── If not children_scanned and is_directory, show "..."
    ├── If not content_compared and not is_directory, show "[pending]"
    └── _Requirements: US5_

  - [ ] 12.2 Update status bar for scanning progress
    ├── Show "Scanning... (N pending)" when scan_queue not empty
    ├── Show "Comparing... (N pending)" when comparison_queue not empty
    ├── Show "Scan complete" when all queues empty
    └── _Requirements: US2, US5_

  - [ ] 12.3 Update difference highlighting for PENDING
    ├── Use neutral color for PENDING status
    ├── Distinguish from IDENTICAL status
    └── _Requirements: US5_

- [ ] 13. Implement proper thread lifecycle management
  - [ ] 13.1 Add _stop_worker_threads() method
    ├── Set self.cancelled = True
    ├── Join all worker threads with timeout
    ├── Clean up resources
    └── _Requirements: US2_

  - [ ] 13.2 Call _stop_worker_threads() in should_close()
    ├── Ensure threads are stopped before closing viewer
    ├── Handle timeout gracefully
    └── _Requirements: US2_

  - [ ] 13.3 Handle thread exceptions
    ├── Wrap worker thread loops in try/except
    ├── Log exceptions
    ├── Set error flag to notify main thread
    └── _Requirements: US2_

- [ ] 14. Checkpoint - Verify thread safety and lifecycle
  └── Ensure no race conditions, deadlocks, or resource leaks

- [ ] 15. Update existing functionality for progressive scanning
  - [ ] 15.1 Update filter to handle PENDING status
    ├── When hiding identical files, also consider PENDING
    ├── Don't hide PENDING files (they might become different)
    └── _Requirements: US5_

  - [ ] 15.2 Update statistics calculation
    ├── Count PENDING items separately
    ├── Update status bar to show pending count
    └── _Requirements: US5_

  - [ ] 15.3 Update file diff opening
    ├── Check if file content has been compared
    ├── If PENDING, compare immediately before opening diff
    └── _Requirements: US2_

- [ ] 16. Add progress animation in status bar
  - [ ] 16.1 Use ProgressAnimator for scanning indicator
    ├── Import tfm_progress_animator
    ├── Create ProgressAnimator instance
    ├── Update animation in render() when scanning
    └── _Requirements: US2_

  - [ ] 16.2 Show progress percentage if available
    ├── Calculate percentage based on queue sizes
    ├── Display in status bar
    └── _Requirements: US2_

- [ ] 17. Create demo script for progressive scanning
  ├── Create `demo/demo_directory_diff_progressive.py`
  ├── Set up large directory structures (1000+ files)
  ├── Demonstrate immediate display
  ├── Show progressive loading in action
  └── _Requirements: US1, US2_

- [ ] 18. Update documentation
  - [ ] 18.1 Update DIRECTORY_DIFF_VIEWER_FEATURE.md
    ├── Document progressive scanning behavior
    ├── Explain pending status indicators
    ├── Note performance improvements
    └── _Requirements: US1, US2, US5_

  - [ ] 18.2 Update DIRECTORY_DIFF_VIEWER_IMPLEMENTATION.md
    ├── Document new architecture with worker threads
    ├── Explain thread synchronization strategy
    ├── Document priority system
    ├── Add diagrams for data flow
    └── _Requirements: US2, US3, US4_

- [ ] 19. Final checkpoint - Integration and performance testing
  ├── Test with very large directory trees (10,000+ files)
  ├── Verify time-to-first-display < 100ms
  ├── Test thread safety with stress testing
  ├── Test priority system with various user interactions
  ├── Test on-demand scanning for deep one-sided trees
  ├── Verify no memory leaks or resource issues
  └── Ensure all tests pass, ask the user if questions arise.

## Notes

- This implementation builds on the existing DirectoryDiffViewer
- Focus on thread safety - use proper locking throughout
- Prioritize user experience - visible items should load first
- Test thoroughly with large directory structures
- Monitor memory usage - don't load entire trees unnecessarily
- Each task references user stories from progressive-scanning spec

## Performance Goals

- **Time to First Display**: < 100ms for typical directories
- **UI Responsiveness**: No blocking during any operation
- **Memory Efficiency**: Only load data for visible/expanded directories
- **Smart Prioritization**: Visible items scanned before hidden ones

## Thread Safety Rules

1. Always acquire `queue_lock` before `data_lock`
2. Always acquire `data_lock` before `tree_lock`
3. Never hold multiple locks when calling external functions
4. Use RLock for reentrant locking where needed
5. Check `cancelled` flag frequently in worker threads
