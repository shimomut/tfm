# Design Document: Drag-and-Drop Support

## Overview

This design implements drag-and-drop functionality for TFM, enabling users to drag files from the file manager to external applications on desktop platforms. The implementation builds on the existing mouse event support infrastructure and integrates with native platform drag-and-drop systems through the TTK backend abstraction layer. The design is platform-agnostic at the TFM level, with platform-specific implementations in the backends (CoreGraphics for macOS, future Windows backend, etc.).

The architecture follows a layered approach:
1. **Gesture Detection Layer**: Detects drag gestures from mouse events (platform-independent)
2. **Payload Preparation Layer**: Prepares file paths for the drag operation (platform-independent)
3. **Backend Integration Layer**: Interfaces with native platform drag-and-drop (platform-specific)
4. **UI Feedback Layer**: Provides visual feedback during drag operations (platform-independent)

**Platform Support**:
- **Current**: macOS via CoreGraphics backend
- **Future**: Windows via future Windows backend, Linux via future X11/Wayland backends
- **Not Supported**: Terminal mode (Curses backend) - gracefully degrades

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                    TFM Application                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Drag Gesture Detector                    │  │
│  │  - Tracks mouse button state                     │  │
│  │  - Calculates movement distance                  │  │
│  │  - Distinguishes click from drag                 │  │
│  └──────────────────────┬───────────────────────────┘  │
│                         │                               │
│  ┌──────────────────────┴───────────────────────────┐  │
│  │         Drag Payload Builder                     │  │
│  │  - Collects selected files or focused item       │  │
│  │  - Converts to absolute file:// URLs             │  │
│  │  - Validates file existence                      │  │
│  │  - Filters out remote/archive files              │  │
│  └──────────────────────┬───────────────────────────┘  │
│                         │                               │
│  ┌──────────────────────┴───────────────────────────┐  │
│  │         Drag Session Manager                     │  │
│  │  - Manages drag lifecycle                        │  │
│  │  - Coordinates with backend                      │  │
│  │  - Handles completion/cancellation               │  │
│  └──────────────────────┬───────────────────────────┘  │
└─────────────────────────┼────────────────────────────────┘
                          │
┌─────────────────────────┼────────────────────────────────┐
│                   TTK Library                           │
│  ┌──────────────────────┴───────────────────────────┐  │
│  │      CoreGraphics Backend                        │  │
│  │  - Initiates native drag session                 │  │
│  │  - Provides file URLs to Pasteboard              │  │
│  │  - Handles drag image creation                   │  │
│  │  - Notifies completion                           │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   macOS Drag System   │
              │  - Manages drag UI    │
              │  - Routes to targets  │
              │  - Handles operations │
              └───────────────────────┘
```

### Drag Operation Flow

1. **Mouse Button Down**: User presses mouse button on a file item
   - Record initial position and timestamp
   - Enter "potential drag" state

2. **Mouse Movement**: User moves mouse with button held
   - Calculate distance from initial position
   - If distance < threshold: remain in "potential drag" state
   - If distance >= threshold: transition to "dragging" state

3. **Drag Initiation**: Threshold exceeded
   - Determine drag payload (selected files or focused item)
   - Validate files (local, exist, not archive contents)
   - Call backend to start native drag session
   - Display drag image

4. **Drag in Progress**: User continues moving mouse
   - OS handles drag cursor and visual feedback
   - TFM ignores other mouse events

5. **Drag Completion**: User releases mouse button
   - OS determines if drop is valid
   - OS performs operation (copy/move/open)
   - Backend notifies TFM of completion
   - TFM returns to normal state

6. **Drag Cancellation**: User presses Escape or drops on invalid target
   - OS cancels drag operation
   - Backend notifies TFM of cancellation
   - TFM returns to normal state

## Components and Interfaces

### DragGestureDetector Class

Detects drag gestures from mouse events:

```python
from dataclasses import dataclass
from typing import Optional
import time

@dataclass
class DragGestureState:
    """Tracks the state of a potential drag gesture."""
    button_down: bool = False
    start_x: int = 0
    start_y: int = 0
    start_time: float = 0.0
    current_x: int = 0
    current_y: int = 0
    dragging: bool = False

class DragGestureDetector:
    """Detects drag gestures from mouse events."""
    
    # Thresholds for drag detection
    DRAG_DISTANCE_THRESHOLD = 5  # pixels
    DRAG_TIME_THRESHOLD = 0.15  # seconds
    
    def __init__(self):
        self.state = DragGestureState()
        self.logger = getLogger("DragGesture")
    
    def handle_button_down(self, x: int, y: int) -> None:
        """
        Handle mouse button down event.
        
        Args:
            x: Mouse x coordinate
            y: Mouse y coordinate
        """
        self.state.button_down = True
        self.state.start_x = x
        self.state.start_y = y
        self.state.current_x = x
        self.state.current_y = y
        self.state.start_time = time.time()
        self.state.dragging = False
    
    def handle_move(self, x: int, y: int) -> bool:
        """
        Handle mouse move event.
        
        Args:
            x: Mouse x coordinate
            y: Mouse y coordinate
            
        Returns:
            True if drag gesture detected, False otherwise
        """
        if not self.state.button_down:
            return False
        
        self.state.current_x = x
        self.state.current_y = y
        
        # Calculate distance from start
        dx = x - self.state.start_x
        dy = y - self.state.start_y
        distance = (dx * dx + dy * dy) ** 0.5
        
        # Check if drag threshold exceeded
        if distance >= self.DRAG_DISTANCE_THRESHOLD:
            if not self.state.dragging:
                self.state.dragging = True
                self.logger.info(f"Drag gesture detected (distance: {distance:.1f})")
                return True
        
        return False
    
    def handle_button_up(self) -> bool:
        """
        Handle mouse button up event.
        
        Returns:
            True if this was a drag gesture, False if it was a click
        """
        was_dragging = self.state.dragging
        self.reset()
        return was_dragging
    
    def reset(self) -> None:
        """Reset gesture state."""
        self.state = DragGestureState()
    
    def is_dragging(self) -> bool:
        """Check if currently in drag state."""
        return self.state.dragging
```

### DragPayloadBuilder Class

Prepares file paths for drag operations:

```python
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote

class DragPayloadBuilder:
    """Builds drag payload from file selections."""
    
    MAX_FILES = 1000  # Maximum files in a single drag
    
    def __init__(self):
        self.logger = getLogger("DragPayload")
    
    def build_payload(
        self,
        selected_files: List[Path],
        focused_item: Optional[Path],
        current_directory: Path
    ) -> Optional[List[str]]:
        """
        Build drag payload from file selections.
        
        Args:
            selected_files: List of selected file paths
            focused_item: Currently focused file path
            current_directory: Current directory path
            
        Returns:
            List of file:// URLs, or None if drag not allowed
        """
        # Determine which files to drag
        if selected_files:
            files_to_drag = selected_files
        elif focused_item:
            # Check if focused item is parent directory marker
            if focused_item.name == "..":
                self.logger.info("Cannot drag parent directory marker")
                return None
            files_to_drag = [focused_item]
        else:
            self.logger.warning("No files to drag")
            return None
        
        # Check file count limit
        if len(files_to_drag) > self.MAX_FILES:
            self.logger.error(f"Too many files to drag: {len(files_to_drag)} > {self.MAX_FILES}")
            return None
        
        # Validate and convert to URLs
        urls = []
        for file_path in files_to_drag:
            # Check if file is remote
            if self._is_remote_file(file_path):
                self.logger.error(f"Cannot drag remote file: {file_path}")
                return None
            
            # Check if file is inside archive
            if self._is_archive_content(file_path):
                self.logger.error(f"Cannot drag archive content: {file_path}")
                return None
            
            # Check if file exists
            if not file_path.exists():
                self.logger.error(f"File does not exist: {file_path}")
                return None
            
            # Convert to absolute file:// URL
            absolute_path = file_path.resolve()
            url = self._path_to_file_url(absolute_path)
            urls.append(url)
        
        self.logger.info(f"Built drag payload with {len(urls)} files")
        return urls
    
    def _is_remote_file(self, path: Path) -> bool:
        """Check if path is a remote file (S3, SSH, etc.)."""
        path_str = str(path)
        return path_str.startswith("s3://") or path_str.startswith("ssh://")
    
    def _is_archive_content(self, path: Path) -> bool:
        """Check if path is inside an archive."""
        # Archive paths contain special markers
        path_str = str(path)
        return "::archive::" in path_str or ".zip/" in path_str or ".tar/" in path_str
    
    def _path_to_file_url(self, path: Path) -> str:
        """
        Convert file path to file:// URL.
        
        Args:
            path: Absolute file path
            
        Returns:
            file:// URL string
        """
        # Convert to POSIX path and URL-encode
        posix_path = path.as_posix()
        encoded_path = quote(posix_path, safe='/')
        return f"file://{encoded_path}"
```

### DragSessionManager Class

Manages drag session lifecycle:

```python
from enum import Enum
from typing import List, Optional, Callable

class DragState(Enum):
    """Drag session states."""
    IDLE = "idle"
    DRAGGING = "dragging"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class DragSessionManager:
    """Manages drag-and-drop session lifecycle."""
    
    def __init__(self, backend):
        self.backend = backend
        self.state = DragState.IDLE
        self.current_urls: Optional[List[str]] = None
        self.completion_callback: Optional[Callable] = None
        self.logger = getLogger("DragSession")
    
    def start_drag(
        self,
        urls: List[str],
        drag_image_text: str,
        completion_callback: Optional[Callable] = None
    ) -> bool:
        """
        Start a drag session.
        
        Args:
            urls: List of file:// URLs to drag
            drag_image_text: Text to display in drag image
            completion_callback: Called when drag completes
            
        Returns:
            True if drag started successfully, False otherwise
        """
        if self.state != DragState.IDLE:
            self.logger.warning(f"Cannot start drag in state: {self.state}")
            return False
        
        # Check backend support
        if not self.backend.supports_drag_and_drop():
            self.logger.error("Backend does not support drag-and-drop")
            return False
        
        # Start native drag session
        success = self.backend.start_drag_session(urls, drag_image_text)
        if not success:
            self.logger.error("Failed to start native drag session")
            return False
        
        self.state = DragState.DRAGGING
        self.current_urls = urls
        self.completion_callback = completion_callback
        self.logger.info(f"Started drag session with {len(urls)} files")
        return True
    
    def handle_drag_completed(self) -> None:
        """Handle drag session completion."""
        if self.state != DragState.DRAGGING:
            return
        
        self.logger.info("Drag session completed")
        self.state = DragState.COMPLETED
        
        if self.completion_callback:
            self.completion_callback(completed=True)
        
        self._cleanup()
    
    def handle_drag_cancelled(self) -> None:
        """Handle drag session cancellation."""
        if self.state != DragState.DRAGGING:
            return
        
        self.logger.info("Drag session cancelled")
        self.state = DragState.CANCELLED
        
        if self.completion_callback:
            self.completion_callback(completed=False)
        
        self._cleanup()
    
    def _cleanup(self) -> None:
        """Clean up drag session resources."""
        self.current_urls = None
        self.completion_callback = None
        self.state = DragState.IDLE
    
    def is_dragging(self) -> bool:
        """Check if drag is in progress."""
        return self.state == DragState.DRAGGING
```

### Backend Interface Extensions

Extend TTK backend interface for drag-and-drop (platform-agnostic):

```python
class TtkBackend:
    """Base backend interface with drag-and-drop support."""
    
    def supports_drag_and_drop(self) -> bool:
        """
        Query whether this backend supports drag-and-drop.
        
        Returns:
            True if drag-and-drop is available, False otherwise.
        """
        return False
    
    def start_drag_session(
        self,
        file_urls: List[str],
        drag_image_text: str
    ) -> bool:
        """
        Start a native drag-and-drop session.
        
        This method initiates a platform-specific drag operation:
        - macOS: Uses NSDraggingSession with NSPasteboard
        - Windows: Uses IDropSource/IDataObject with OLE drag-drop
        - Linux: Uses X11 drag-and-drop or Wayland data device
        
        The file_urls parameter uses the file:// URI scheme which is
        cross-platform compatible (RFC 8089).
        
        Args:
            file_urls: List of file:// URLs to drag (platform-independent format)
            drag_image_text: Text to display in drag image
            
        Returns:
            True if drag started successfully, False otherwise.
        """
        raise NotImplementedError
    
    def set_drag_completion_callback(self, callback: Callable) -> None:
        """
        Set callback for drag completion/cancellation.
        
        The callback will be invoked with a boolean parameter:
        - True if drag completed successfully (dropped on valid target)
        - False if drag was cancelled
        
        Args:
            callback: Function to call when drag completes
        """
        self.drag_completion_callback = callback
```

### CoreGraphics Backend Implementation

Implement drag-and-drop in CoreGraphics backend (macOS-specific):

```python
class CoreGraphicsBackend(TtkBackend):
    """macOS CoreGraphics backend with drag-and-drop support."""
    
    def supports_drag_and_drop(self) -> bool:
        """CoreGraphics backend supports drag-and-drop on macOS."""
        return True
    
    def start_drag_session(
        self,
        file_urls: List[str],
        drag_image_text: str
    ) -> bool:
        """
        Start a native macOS drag session.
        
        This method calls into the C++ extension to:
        1. Create an NSDraggingItem with file URLs
        2. Set up the drag image with text
        3. Begin the drag session with NSDraggingSession
        4. Register callbacks for completion/cancellation
        
        macOS-specific implementation details:
        - Uses NSPasteboard with NSFilenamesPboardType
        - Creates NSDraggingItem for each file URL
        - Generates drag image using NSImage with text overlay
        - Supports standard macOS drag modifiers (Option, Command)
        
        Args:
            file_urls: List of file:// URLs to drag
            drag_image_text: Text to display in drag image
            
        Returns:
            True if drag started successfully, False otherwise.
        """
        try:
            # Call C++ extension to start native drag
            # Implementation in coregraphics_backend.cpp
            success = self._native_start_drag(file_urls, drag_image_text)
            return success
        except Exception as e:
            self.logger.error(f"Failed to start drag session: {e}")
            return False
    
    def _on_drag_completed(self) -> None:
        """
        Called by C++ extension when drag completes.
        
        Notifies the application via callback.
        """
        if hasattr(self, 'drag_completion_callback'):
            self.drag_completion_callback(completed=True)
    
    def _on_drag_cancelled(self) -> None:
        """
        Called by C++ extension when drag is cancelled.
        
        Notifies the application via callback.
        """
        if hasattr(self, 'drag_completion_callback'):
            self.drag_completion_callback(completed=False)
```

### Future Windows Backend Implementation

Placeholder for future Windows backend (Windows-specific):

```python
class WindowsBackend(TtkBackend):
    """
    Future Windows backend with drag-and-drop support.
    
    Implementation notes for future development:
    - Use IDropSource and IDataObject COM interfaces
    - Provide file paths via CF_HDROP clipboard format
    - Use DoDragDrop() to initiate drag operation
    - Handle DROPEFFECT_COPY, DROPEFFECT_MOVE, DROPEFFECT_LINK
    - Create drag image using IDropTargetHelper
    """
    
    def supports_drag_and_drop(self) -> bool:
        """Windows backend will support drag-and-drop."""
        return True
    
    def start_drag_session(
        self,
        file_urls: List[str],
        drag_image_text: str
    ) -> bool:
        """
        Start a native Windows drag session.
        
        Future implementation will:
        1. Convert file:// URLs to Windows paths
        2. Create IDataObject with CF_HDROP format
        3. Create IDropSource implementation
        4. Call DoDragDrop() to start drag
        5. Handle completion via IDropSource callbacks
        
        Args:
            file_urls: List of file:// URLs to drag
            drag_image_text: Text to display in drag image
            
        Returns:
            True if drag started successfully, False otherwise.
        """
        # Future implementation
        raise NotImplementedError("Windows drag-and-drop not yet implemented")
```

### Curses Backend Implementation

Curses backend does not support drag-and-drop:

```python
class CursesBackend(TtkBackend):
    """Terminal curses backend without drag-and-drop support."""
    
    def supports_drag_and_drop(self) -> bool:
        """Curses backend does not support drag-and-drop."""
        return False
    
    def start_drag_session(
        self,
        file_urls: List[str],
        drag_image_text: str
    ) -> bool:
        """
        Drag-and-drop not supported in terminal mode.
        
        Returns:
            False (drag not supported)
        """
        self.logger.info("Drag-and-drop not supported in terminal mode")
        return False
```

### FileManager Integration

Integrate drag-and-drop into TFM FileManager:

```python
class FileManager:
    """Main file manager with drag-and-drop support."""
    
    def __init__(self, backend):
        self.backend = backend
        self.gesture_detector = DragGestureDetector()
        self.payload_builder = DragPayloadBuilder()
        self.drag_manager = DragSessionManager(backend)
        self.logger = getLogger("FileManager")
    
    def handle_mouse_event(self, event: MouseEvent) -> bool:
        """
        Handle mouse events including drag gestures.
        
        Args:
            event: Mouse event to handle
            
        Returns:
            True if event was handled
        """
        # If drag in progress, ignore other events
        if self.drag_manager.is_dragging():
            return True
        
        # Handle button down
        if event.event_type == MouseEventType.BUTTON_DOWN:
            self.gesture_detector.handle_button_down(event.column, event.row)
            # Also handle click-to-focus as before
            return self._handle_click(event)
        
        # Handle move - check for drag gesture
        elif event.event_type == MouseEventType.MOVE:
            if self.gesture_detector.handle_move(event.column, event.row):
                # Drag gesture detected - initiate drag
                return self._initiate_drag()
        
        # Handle button up
        elif event.event_type == MouseEventType.BUTTON_UP:
            was_dragging = self.gesture_detector.handle_button_up()
            if not was_dragging:
                # Was a click, not a drag
                return self._handle_click_release(event)
        
        return False
    
    def _initiate_drag(self) -> bool:
        """
        Initiate a drag operation.
        
        Returns:
            True if drag started successfully
        """
        # Get selected files or focused item
        selected_files = self._get_selected_files()
        focused_item = self._get_focused_item()
        current_dir = self._get_current_directory()
        
        # Build drag payload
        urls = self.payload_builder.build_payload(
            selected_files,
            focused_item,
            current_dir
        )
        
        if not urls:
            # Payload building failed (remote files, etc.)
            self.gesture_detector.reset()
            return False
        
        # Create drag image text
        if len(urls) == 1:
            drag_text = focused_item.name if focused_item else "1 file"
        else:
            drag_text = f"{len(urls)} files"
        
        # Start drag session
        success = self.drag_manager.start_drag(
            urls,
            drag_text,
            completion_callback=self._on_drag_completed
        )
        
        if not success:
            self.gesture_detector.reset()
            return False
        
        self.logger.info(f"Drag initiated: {drag_text}")
        return True
    
    def _on_drag_completed(self, completed: bool) -> None:
        """
        Called when drag session completes or is cancelled.
        
        Args:
            completed: True if drag completed, False if cancelled
        """
        if completed:
            self.logger.info("Drag completed successfully")
        else:
            self.logger.info("Drag was cancelled")
        
        # Reset gesture detector
        self.gesture_detector.reset()
        
        # Redraw UI to restore normal state
        self._request_redraw()
```

## Data Models

### Drag Gesture State Machine

```
┌──────┐  button_down   ┌───────────────┐
│ IDLE ├───────────────>│ BUTTON_DOWN   │
└──────┘                └───────┬───────┘
                                │
                                │ move < threshold
                                │ (stay in state)
                                │
                                │ move >= threshold
                                ▼
                        ┌───────────────┐
                        │   DRAGGING    │
                        └───────┬───────┘
                                │
                    ┌───────────┼───────────┐
                    │                       │
              button_up                button_up
              (valid drop)             (invalid drop)
                    │                       │
                    ▼                       ▼
            ┌───────────────┐       ┌──────────────┐
            │   COMPLETED   │       │  CANCELLED   │
            └───────┬───────┘       └──────┬───────┘
                    │                       │
                    └───────────┬───────────┘
                                │
                                ▼
                            ┌──────┐
                            │ IDLE │
                            └──────┘
```

### File URL Format

File paths are converted to file:// URLs following RFC 8089 (cross-platform standard):

```
file://[host]/path

Examples (macOS/Linux):
- Local file: file:///Users/username/Documents/file.txt
- With spaces: file:///Users/username/My%20Documents/file.txt
- Special chars: file:///Users/username/file%20%28copy%29.txt

Examples (Windows - future):
- Local file: file:///C:/Users/username/Documents/file.txt
- UNC path: file://server/share/file.txt
- With spaces: file:///C:/Users/username/My%20Documents/file.txt
```

**Platform-Specific Handling**:
- **macOS**: Backend converts file:// URLs to NSURLs for NSDraggingItem
- **Windows** (future): Backend converts file:// URLs to Windows paths for CF_HDROP
- **Linux** (future): Backend uses file:// URLs directly with X11/Wayland protocols

### Drag Payload Structure

The drag payload structure is platform-independent at the TFM level:

**TFM Layer** (platform-independent):
- **Format**: Array of file:// URL strings (RFC 8089)
- **Count**: Number of files (1 to MAX_FILES)
- **Metadata**: File names for drag image display

**Backend Layer** (platform-specific):
- **macOS**: NSFilenamesPboardType with NSURLs
- **Windows** (future): CF_HDROP with Windows paths
- **Linux** (future): text/uri-list MIME type with file:// URLs

## Data Models

### Coordinate Mapping

Drag gestures use pixel coordinates (not text grid coordinates) for accurate distance calculation:

```python
# Mouse event provides both coordinate systems
event.column, event.row          # Text grid coordinates
event.pixel_x, event.pixel_y     # Pixel coordinates (for drag distance)
```

## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property Reflection

After analyzing all acceptance criteria, several redundancies were identified:
- Requirements 6.2 and 6.3 are covered by 1.5 (threshold behavior)
- Requirements 8.4 is covered by 1.4 (parent directory marker)
- Requirements 8.5 is covered by 2.5 and 4.2 (state restoration)
- Requirements 9.4 is covered by 9.1 (archive content detection)
- Requirements 7.1 extends 1.2 by adding order preservation

The following properties eliminate these redundancies while ensuring comprehensive coverage.

### Core Properties

**Property 1: Drag initiation on movement threshold**
*For any* file item and mouse movement sequence, when the mouse button is pressed and movement exceeds the threshold distance, a drag session must be initiated.
**Validates: Requirements 1.1, 1.5, 6.2, 6.3**

**Property 2: Payload contains selected files**
*For any* non-empty set of selected files, the drag payload must contain exactly those files in the same order.
**Validates: Requirements 1.2, 7.1**

**Property 3: Payload contains focused item when no selection**
*For any* focused item with an empty selection set, the drag payload must contain only that focused item.
**Validates: Requirements 1.3**

**Property 4: Drag image shows file count**
*For any* drag session, the drag image must display either the filename (for single file) or the count in format "N files" (for multiple files).
**Validates: Requirements 2.1, 2.2, 2.3**

**Property 5: State restoration on cancellation**
*For any* drag session that is cancelled, the UI state must be restored to the state before the drag began.
**Validates: Requirements 2.5, 4.2, 8.5**

**Property 6: Absolute file:// URLs in payload**
*For any* file in the drag payload, its path must be absolute and formatted as a file:// URL.
**Validates: Requirements 3.1, 3.2**

**Property 7: Remote files rejected**
*For any* file path starting with s3:// or ssh://, attempting to drag that file must not initiate a drag session.
**Validates: Requirements 3.4**

**Property 8: File existence validation**
*For any* drag payload, all files must exist on the filesystem before the drag session starts.
**Validates: Requirements 3.5**

**Property 9: Backend registration on drag start**
*For any* drag session, the backend's start_drag_session method must be called with the file URLs.
**Validates: Requirements 4.1**

**Property 10: Resource cleanup on completion**
*For any* drag session that completes or is cancelled, all drag-related resources (state, callbacks, URLs) must be cleaned up.
**Validates: Requirements 4.2**

**Property 11: Event blocking during drag**
*For any* mouse event that occurs while a drag is in progress, that event must not be processed by the drag source component.
**Validates: Requirements 4.3**

**Property 12: State machine transitions**
*For any* sequence of drag operations, the state must transition correctly: IDLE → DRAGGING → (COMPLETED | CANCELLED) → IDLE.
**Validates: Requirements 4.4**

**Property 13: Cancellation callback handling**
*For any* drag session that is cancelled by the OS, the cancellation callback must be invoked and state must return to IDLE.
**Validates: Requirements 4.5, 5.3**

**Property 14: Graceful degradation in terminal mode**
*For any* drag operation attempted in Curses backend mode, the operation must return False without raising exceptions.
**Validates: Requirements 5.4**

**Property 15: Time threshold for drag detection**
*For any* mouse button press followed by movement, if the movement occurs within the time threshold and below distance threshold, it must be treated as a click, not a drag.
**Validates: Requirements 6.5**

**Property 16: Selection state preservation**
*For any* drag operation, the selection state before the drag must be identical to the selection state after the drag completes or is cancelled.
**Validates: Requirements 7.4**

**Property 17: Files and directories in payload**
*For any* selection containing both files and directories, the drag payload must include both types.
**Validates: Requirements 7.5**

**Property 18: Error handling for OS rejection**
*For any* drag session where the OS rejects the drag, an error must be logged and the state must return to IDLE.
**Validates: Requirements 8.3**

**Property 19: Archive content rejection**
*For any* file path containing archive markers (::archive::, .zip/, .tar/), attempting to drag that file must not initiate a drag session.
**Validates: Requirements 9.1, 9.4**

**Property 20: Archive file vs content distinction**
*For any* file path, if it points to an archive file itself (not contents within), dragging must be allowed; if it points to contents within an archive, dragging must be prevented.
**Validates: Requirements 9.3**

## Error Handling

### Drag Initiation Errors

**Scenario**: User attempts to drag remote files (S3, SSH)
- **Detection**: DragPayloadBuilder detects remote path prefix
- **Response**: Return None from build_payload, log info message
- **User Impact**: Drag does not start, optional error message shown

**Scenario**: User attempts to drag parent directory marker ("..")
- **Detection**: DragPayloadBuilder checks for ".." filename
- **Response**: Return None from build_payload, no error message
- **User Impact**: Drag does not start, no visual feedback (expected behavior)

**Scenario**: User attempts to drag files from within archive
- **Detection**: DragPayloadBuilder detects archive path markers
- **Response**: Return None from build_payload, show error message
- **User Impact**: Drag does not start, message explains extraction needed

**Scenario**: File no longer exists when drag starts
- **Detection**: DragPayloadBuilder validates file existence
- **Response**: Return None from build_payload, show error message
- **User Impact**: Drag does not start, message explains file missing

**Scenario**: Too many files selected (> 1000)
- **Detection**: DragPayloadBuilder checks file count
- **Response**: Return None from build_payload, show error message
- **User Impact**: Drag does not start, message explains limit

### Drag Session Errors

**Scenario**: Backend fails to start native drag session
- **Detection**: start_drag_session returns False
- **Response**: Log error, reset gesture detector, return to IDLE
- **User Impact**: Drag does not start, no visual feedback

**Scenario**: OS rejects drag operation
- **Detection**: Backend receives rejection from OS
- **Response**: Log error, invoke cancellation callback, cleanup
- **User Impact**: Drag appears to cancel, state restored

**Scenario**: Exception during drag completion callback
- **Detection**: Try-catch in callback invocation
- **Response**: Log error, continue with cleanup
- **User Impact**: Drag completes but callback side effects may not occur

### Backend Capability Errors

**Scenario**: Drag attempted in Curses backend (terminal mode)
- **Detection**: supports_drag_and_drop returns False
- **Response**: Return False from start_drag, log info message
- **User Impact**: Drag does not start, no error (expected limitation)

**Scenario**: Backend not initialized properly
- **Detection**: Backend reference is None or invalid
- **Response**: Return False from start_drag, log error
- **User Impact**: Drag does not start, application continues

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests** focus on:
- Specific examples of drag gestures with known coordinates
- Edge cases (parent directory, remote files, archive contents)
- Error conditions (missing files, too many files, OS rejection)
- State transitions through the drag lifecycle
- Callback invocation on completion/cancellation

**Property-Based Tests** focus on:
- Universal properties across all possible inputs
- Drag threshold behavior for arbitrary mouse movements
- Payload building for arbitrary file selections
- State machine correctness for arbitrary operation sequences
- URL formatting for arbitrary file paths

### Property-Based Testing Configuration

- **Library**: Use `hypothesis` for Python property-based testing
- **Iterations**: Minimum 100 iterations per property test
- **Tagging**: Each test must reference its design property with format:
  ```python
  # Feature: drag-and-drop, Property 1: Drag initiation on movement threshold
  ```

### Test Organization

```
test/
├── test_drag_gesture_detection.py         # Properties 1, 15 (PBT)
├── test_drag_payload_building.py          # Properties 2, 3, 6, 7, 8, 17, 19, 20 (PBT)
├── test_drag_visual_feedback.py           # Property 4 (PBT)
├── test_drag_session_lifecycle.py         # Properties 9, 10, 11, 12, 13 (PBT)
├── test_drag_state_restoration.py         # Properties 5, 16 (PBT)
├── test_drag_backend_integration.py       # Properties 14, 18 (PBT + unit)
├── test_drag_error_handling.py            # Unit tests for error scenarios
├── test_drag_edge_cases.py                # Unit tests for edge cases
└── test_drag_integration.py               # End-to-end integration tests
```

### Example Property Test

```python
from hypothesis import given, strategies as st
from pathlib import Path

# Feature: drag-and-drop, Property 2: Payload contains selected files
@given(
    selected_files=st.lists(
        st.builds(Path, st.text(min_size=1, max_size=50)),
        min_size=1,
        max_size=100
    )
)
def test_payload_contains_selected_files_in_order(selected_files, tmp_path):
    """Drag payload must contain all selected files in order."""
    # Create actual files
    actual_files = []
    for i, file_path in enumerate(selected_files):
        actual_file = tmp_path / f"file_{i}.txt"
        actual_file.write_text("test")
        actual_files.append(actual_file)
    
    # Build payload
    builder = DragPayloadBuilder()
    urls = builder.build_payload(
        selected_files=actual_files,
        focused_item=None,
        current_directory=tmp_path
    )
    
    # Verify all files present in order
    assert urls is not None
    assert len(urls) == len(actual_files)
    
    for i, (url, file_path) in enumerate(zip(urls, actual_files)):
        expected_url = f"file://{file_path.resolve().as_posix()}"
        assert url == expected_url, f"File {i} URL mismatch"
```

### Integration Testing

Integration tests verify the complete flow from mouse gesture through to backend drag initiation:

1. **Gesture Detection Test**: Simulate mouse events and verify drag detection
2. **Payload Building Test**: Verify file selection translates to correct URLs
3. **Backend Integration Test**: Verify backend methods called correctly
4. **State Management Test**: Verify state transitions through complete lifecycle
5. **Error Recovery Test**: Verify graceful handling of all error conditions

### Manual Testing

Manual testing required for:
- Visual verification of drag image appearance
- Real drag-and-drop to external applications (Finder, text editors)
- Drag cursor feedback during operation
- Multi-file drag with large selections
- Edge cases like dragging to invalid targets

