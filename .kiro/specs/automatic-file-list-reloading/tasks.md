# Implementation Plan: Automatic File List Reloading

## Overview

This implementation plan breaks down the automatic file list reloading feature into discrete coding tasks. The feature uses the watchdog library for cross-platform filesystem monitoring, implements a queue-based threading model for safe communication between the monitor thread and main UI thread, and provides comprehensive error handling with graceful degradation to polling mode when native monitoring is unavailable.

## Tasks

- [ ] 1. Set up dependencies and project structure
  - Add watchdog library to project dependencies
  - Create src/tfm_file_monitor_manager.py module
  - Create src/tfm_file_monitor_observer.py module
  - Set up imports in FileManager for monitoring components
  - _Requirements: 5.1, 5.2, 5.3, 6.2_

- [ ] 2. Implement configuration schema and loading
  - [ ] 2.1 Add file_monitoring configuration section to TFM config schema
    - Add enabled, coalesce_delay_ms, max_reloads_per_second, suppress_after_action_ms, fallback_poll_interval_s fields
    - Implement default values (enabled=true, coalesce_delay_ms=200, max_reloads_per_second=5, suppress_after_action_ms=1000, fallback_poll_interval_s=5)
    - Add configuration validation logic
    - _Requirements: 10.1, 10.2, 11.1, 11.2, 11.3_
  
  - [ ]* 2.2 Write unit tests for configuration loading
    - Test default values
    - Test custom configuration values
    - Test invalid configuration handling
    - _Requirements: 10.1_

- [ ] 3. Implement FileMonitorObserver class
  - [ ] 3.1 Create FileMonitorObserver class with watchdog integration
    - Implement __init__(path, event_callback, logger) constructor
    - Implement start() method to initialize watchdog Observer
    - Implement stop() method for cleanup
    - Implement is_alive() status check
    - Implement get_monitoring_mode() to return "native" or "polling"
    - Add error handling for initialization failures
    - _Requirements: 5.1, 5.2, 5.3, 6.1, 6.2, 7.4_
  
  - [ ] 3.2 Implement TFMFileSystemEventHandler class
    - Create event handler class extending watchdog.events.FileSystemEventHandler
    - Implement on_created() to detect file creation
    - Implement on_deleted() to detect file deletion
    - Implement on_modified() to detect file modification
    - Implement on_moved() to detect file rename/move operations
    - Add filtering logic to ignore subdirectory events (only watch immediate children)
    - Handle move-in events as creation (4.3)
    - Handle move-out events as deletion (4.4)
    - _Requirements: 1.1, 2.1, 3.1, 3.4, 4.1, 4.2, 4.3, 4.4, 1.4, 2.4_
  
  - [ ]* 3.3 Write property test for FileMonitorObserver
    - **Property 1: Filesystem Event Detection**
    - **Validates: Requirements 1.1, 2.1, 3.1, 4.1**
    - Generate random file operations (create, delete, modify, rename)
    - Verify all events are detected and reported
    - _Requirements: 1.1, 2.1, 3.1, 4.1_
  
  - [ ]* 3.4 Write property test for subdirectory filtering
    - **Property 3: Subdirectory Event Filtering**
    - **Validates: Requirements 1.4, 2.4**
    - Generate random subdirectory operations
    - Verify subdirectory events do not trigger parent directory reloads
    - _Requirements: 1.4, 2.4_
  
  - [ ]* 3.5 Write unit tests for event handler
    - Test each event type (create, delete, modify, rename) with specific examples
    - Test move-in and move-out detection
    - Test subdirectory event filtering
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 4.3, 4.4, 1.4, 2.4_

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement FileMonitorManager class
  - [ ] 5.1 Create FileMonitorManager class structure
    - Implement __init__(config, file_manager) constructor
    - Initialize logger with name "FileMonitor"
    - Store reference to file_manager.reload_queue for thread-safe communication
    - Initialize monitoring state dictionaries for left and right panes
    - Set up event coalescing timer and rate limiting state
    - _Requirements: 12.4, 11.1, 11.3_
  
  - [ ] 5.2 Implement monitoring lifecycle methods
    - Implement start_monitoring(left_path, right_path) to start dual-pane monitoring
    - Implement update_monitored_directory(pane_name, new_path) for directory navigation
    - Implement stop_monitoring() for cleanup
    - Implement is_monitoring_enabled() status check
    - Implement get_monitoring_mode(path) to return monitoring mode for a path
    - Add logic to detect unsupported backends (S3, network mounts) and use fallback mode
    - _Requirements: 7.1, 7.2, 6.1, 6.2, 6.4, 6.5_
  
  - [ ] 5.3 Implement event coalescing and rate limiting
    - Implement event coalescing with 200ms window (batch multiple events into single reload)
    - Implement rate limiting (max 5 reloads per second)
    - Implement suppress_reloads(duration_ms) for suppression after user actions
    - Track last reload time per pane
    - Use threading.Timer for coalescing delay
    - _Requirements: 1.3, 2.3, 3.3, 11.1, 11.2, 11.3, 11.4_
  
  - [ ] 5.4 Implement reload request posting
    - Implement _post_reload_request(pane_name) to post to file_manager.reload_queue
    - Ensure thread-safe queue operations
    - Add logging for reload requests
    - _Requirements: 12.2_
  
  - [ ] 5.5 Implement error handling and recovery
    - Add error handling in event callbacks
    - Implement reinitialization logic with retry (up to 3 attempts with exponential backoff)
    - Implement fallback to polling mode after repeated failures
    - Add logging for errors, mode transitions, and recovery attempts
    - _Requirements: 9.1, 9.2, 9.3, 12.3, 12.5_
  
  - [ ]* 5.6 Write property test for event coalescing
    - **Property 2: Event Coalescing**
    - **Validates: Requirements 1.3, 2.3, 3.3, 11.1**
    - Generate random sequences of events within coalescing window
    - Verify events are batched into single reload
    - _Requirements: 1.3, 2.3, 3.3, 11.1_
  
  - [ ]* 5.7 Write property test for rate limiting
    - **Property 19: Rate Limiting**
    - **Validates: Requirements 11.3**
    - Generate high-frequency event sequences
    - Verify reload rate does not exceed configured maximum
    - _Requirements: 11.3_
  
  - [ ]* 5.8 Write property test for error resilience
    - **Property 13: Error Resilience**
    - **Validates: Requirements 9.1**
    - Inject random errors during event processing
    - Verify monitoring continues after errors
    - _Requirements: 9.1_
  
  - [ ]* 5.9 Write unit tests for FileMonitorManager
    - Test dual-pane monitoring initialization
    - Test directory navigation updates
    - Test monitoring enable/disable
    - Test fallback mode detection for S3 and network paths
    - Test error recovery and retry logic
    - _Requirements: 7.1, 7.2, 6.4, 6.5, 9.2, 9.3_

- [ ] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Integrate FileMonitorManager with FileManager
  - [ ] 7.1 Add reload_queue to FileManager
    - Import queue module in FileManager
    - Add self.reload_queue = queue.Queue() in FileManager.__init__()
    - _Requirements: Threading model_
  
  - [ ] 7.2 Initialize FileMonitorManager in FileManager
    - Create FileMonitorManager instance in FileManager.__init__()
    - Pass config and self reference to FileMonitorManager
    - Call start_monitoring() with initial left and right paths
    - Add monitoring cleanup in FileManager shutdown/cleanup
    - _Requirements: 10.2_
  
  - [ ] 7.3 Implement reload queue processing in main event loop
    - Add reload queue check at start of FileManager.run() main loop
    - Implement _handle_reload_request(pane_name) method
    - Call appropriate refresh_files() method for the pane
    - Call mark_dirty() to trigger redraw
    - Use queue.get_nowait() with try/except queue.Empty
    - _Requirements: 1.2, 2.2, 3.2, 4.2_
  
  - [ ] 7.4 Update directory navigation to notify monitor
    - Call file_monitor_manager.update_monitored_directory() in navigate_to_dir()
    - Pass pane name and new path to monitor manager
    - Implement suppression of automatic reloads for 1 second after navigation
    - _Requirements: 7.1, 7.2, 7.3, 11.2_
  
  - [ ] 7.5 Implement user context preservation during reloads
    - Store current cursor position and selected filename before reload
    - After reload, restore cursor to same filename if it still exists
    - If selected file deleted, position cursor on nearest file by alphabetical order
    - Preserve scroll position when possible
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  
  - [ ]* 7.6 Write property test for selection preservation
    - **Property 10: Selection Preservation on Reload**
    - **Validates: Requirements 8.1, 8.2**
    - Generate random file changes while file is selected
    - Verify cursor remains on same file if it still exists
    - _Requirements: 8.1, 8.2_
  
  - [ ]* 7.7 Write property test for cursor repositioning
    - **Property 11: Cursor Repositioning After Deletion**
    - **Validates: Requirements 8.3**
    - Delete currently selected file
    - Verify cursor moves to nearest file by alphabetical order
    - _Requirements: 8.3_
  
  - [ ]* 7.8 Write integration tests for FileManager integration
    - Test monitoring lifecycle with FileManager
    - Test reload queue processing
    - Test directory navigation updates monitoring
    - Test user context preservation across reloads
    - Test suppression after user actions
    - _Requirements: 7.1, 7.2, 8.1, 8.2, 8.3, 8.4, 11.2_

- [ ] 8. Implement runtime monitoring toggle
  - [ ] 8.1 Add toggle_monitoring() method to FileManager
    - Implement method to enable/disable monitoring at runtime
    - Call file_monitor_manager.stop_monitoring() when disabling
    - Call file_monitor_manager.start_monitoring() when enabling
    - Update configuration state
    - _Requirements: 10.4_
  
  - [ ]* 8.2 Write unit tests for runtime toggle
    - Test enabling monitoring at runtime
    - Test disabling monitoring at runtime
    - Verify no automatic reloads when disabled
    - _Requirements: 10.4_

- [ ] 9. Add comprehensive logging
  - [ ] 9.1 Add initialization logging
    - Log monitoring mode (native/polling/disabled) on initialization
    - Log watched directories on start_monitoring()
    - _Requirements: 12.1_
  
  - [ ] 9.2 Add event logging
    - Log each detected filesystem event with event type and filename
    - Log reload requests posted to queue
    - _Requirements: 12.2_
  
  - [ ] 9.3 Add error and transition logging
    - Log all errors with context for debugging
    - Log monitoring mode transitions with reasons
    - Log retry attempts and fallback mode activation
    - _Requirements: 12.3, 12.5_
  
  - [ ]* 9.4 Write unit tests for logging
    - Verify initialization messages are logged
    - Verify event messages are logged
    - Verify error messages are logged with context
    - Verify mode transition messages are logged
    - _Requirements: 12.1, 12.2, 12.3, 12.5_

- [ ] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Handle platform-specific monitoring
  - [ ] 11.1 Add platform detection logic
    - Detect Linux and verify inotify availability
    - Detect macOS and verify FSEvents availability
    - Detect Windows and verify ReadDirectoryChangesW availability
    - Log detected platform and monitoring API
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [ ]* 11.2 Write unit tests for platform detection
    - Test Linux/inotify detection
    - Test macOS/FSEvents detection
    - Test Windows/ReadDirectoryChangesW detection
    - Test fallback when native API unavailable
    - _Requirements: 5.1, 5.2, 5.3, 6.1, 6.2_

- [ ] 12. Implement fallback polling mode
  - [ ] 12.1 Add polling observer implementation
    - Configure watchdog to use PollingObserver when native monitoring unavailable
    - Set polling interval to 5 seconds (configurable)
    - Add detection logic for S3 paths, network mounts, and other unsupported backends
    - _Requirements: 6.2, 6.3, 6.4, 6.5_
  
  - [ ]* 12.2 Write property test for fallback mode
    - **Property 7: Unsupported Backend Fallback**
    - **Validates: Requirements 6.1, 6.2**
    - Test with various unsupported storage backends
    - Verify automatic fallback to polling mode
    - _Requirements: 6.1, 6.2_
  
  - [ ]* 12.3 Write unit tests for polling mode
    - Test polling mode initialization
    - Test polling interval configuration
    - Test S3 path detection and fallback
    - Test network mount detection and fallback
    - _Requirements: 6.2, 6.3, 6.4, 6.5_

- [ ] 13. Add status indicator for fallback mode
  - [ ] 13.1 Implement status indicator in UI
    - Add visual indicator when operating in fallback mode due to errors
    - Display indicator in status bar or appropriate UI location
    - Update indicator when monitoring mode changes
    - _Requirements: 9.4_
  
  - [ ]* 13.2 Write unit tests for status indicator
    - Test indicator appears in fallback mode
    - Test indicator updates on mode changes
    - Test indicator hidden in native mode
    - _Requirements: 9.4_

- [ ] 14. Final integration and end-to-end testing
  - [ ] 14.1 Perform end-to-end testing
    - Test complete workflow: start TFM, create file externally, verify automatic reload
    - Test dual-pane monitoring with changes in both panes
    - Test directory navigation with monitoring updates
    - Test configuration enable/disable
    - Test runtime toggle
    - Test error scenarios and recovery
    - _Requirements: All requirements_
  
  - [ ]* 14.2 Write property test for dual-pane monitoring
    - **Property: Dual-Pane Independence**
    - Generate random events in both left and right panes
    - Verify each pane reloads independently
    - Verify events in one pane don't trigger reload in other pane
    - _Requirements: Dual-pane monitoring_
  
  - [ ]* 14.3 Write property test for monitoring transition
    - **Property 8: Directory Navigation Monitoring Transition**
    - **Validates: Requirements 7.1, 7.2**
    - Navigate through random directory sequences
    - Verify monitoring stops for old directory and starts for new directory
    - _Requirements: 7.1, 7.2_

- [ ] 15. Update documentation
  - [ ] 15.1 Create end-user documentation
    - Create doc/FILE_MONITORING_FEATURE.md
    - Document automatic file list reloading feature
    - Explain configuration options
    - Explain runtime toggle
    - Explain fallback mode indicator
    - Provide troubleshooting guidance
    - _Requirements: All requirements_
  
  - [ ] 15.2 Create developer documentation
    - Create doc/dev/FILE_MONITORING_IMPLEMENTATION.md
    - Document architecture and component interactions
    - Document threading model and queue-based communication
    - Document error handling and recovery strategies
    - Document platform-specific monitoring details
    - Document testing approach and property-based tests
    - _Requirements: All requirements_

- [ ] 16. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at reasonable breaks
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The threading model uses queue.Queue for thread-safe communication between monitor thread and main UI thread
- All logging uses TFM's unified logging system with logger name "FileMonitor"
- The watchdog library provides cross-platform filesystem monitoring with native API support
