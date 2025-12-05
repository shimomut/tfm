"""
UI Backend Abstraction Layer for TFM

This module defines the abstract interface that both TUI (curses) and GUI (Qt)
backends must implement. This abstraction allows the same business logic to work
with different UI implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, List, Any, Set


@dataclass
class InputEvent:
    """
    Represents a unified user input event.
    
    This class provides a common representation for input events from different
    UI backends (curses, Qt, etc.), allowing business logic to handle input
    in a UI-agnostic way.
    """
    type: str  # 'key', 'mouse', 'resize'
    key: Optional[int] = None  # Key code for keyboard events
    key_name: Optional[str] = None  # Human-readable key name (e.g., 'F1', 'Enter')
    mouse_x: Optional[int] = None  # Mouse X coordinate
    mouse_y: Optional[int] = None  # Mouse Y coordinate
    mouse_button: Optional[int] = None  # Mouse button number (1=left, 2=middle, 3=right)
    modifiers: Set[str] = field(default_factory=set)  # 'ctrl', 'shift', 'alt', 'meta'


@dataclass
class LayoutInfo:
    """
    UI layout dimensions for rendering components.
    
    This dataclass defines the positions and sizes of all UI components,
    calculated based on the current screen/window size.
    """
    screen_height: int
    screen_width: int
    left_pane_width: int
    right_pane_width: int
    pane_height: int
    log_height: int
    header_y: int
    panes_y: int
    footer_y: int
    status_y: int
    log_y: int
    
    @staticmethod
    def calculate(screen_height: int, screen_width: int, log_ratio: float = 0.0) -> 'LayoutInfo':
        """
        Calculate layout dimensions for any screen size.
        
        Args:
            screen_height: Total screen/window height
            screen_width: Total screen/window width
            log_ratio: Ratio of screen height to use for log pane (0.0 to 1.0)
        
        Returns:
            LayoutInfo with calculated dimensions
        """
        # Reserve space for header, footer, and status bar
        header_height = 1
        footer_height = 1
        status_height = 1
        
        # Calculate log pane height
        log_height = int(screen_height * log_ratio) if log_ratio > 0 else 0
        
        # Calculate pane height (remaining space after header, footer, status, log)
        pane_height = screen_height - header_height - footer_height - status_height - log_height
        
        # Split width evenly between left and right panes
        left_pane_width = screen_width // 2
        right_pane_width = screen_width - left_pane_width
        
        # Calculate Y positions
        header_y = 0
        panes_y = header_y + header_height
        footer_y = panes_y + pane_height
        status_y = footer_y + footer_height
        log_y = status_y + status_height
        
        return LayoutInfo(
            screen_height=screen_height,
            screen_width=screen_width,
            left_pane_width=left_pane_width,
            right_pane_width=right_pane_width,
            pane_height=pane_height,
            log_height=log_height,
            header_y=header_y,
            panes_y=panes_y,
            footer_y=footer_y,
            status_y=status_y,
            log_y=log_y
        )


@dataclass
class DialogConfig:
    """
    Configuration for displaying dialogs.
    
    This dataclass provides a unified way to configure dialogs across
    different UI backends.
    """
    type: str  # 'confirmation', 'input', 'list', 'info', 'progress'
    title: str
    message: str
    choices: Optional[List[Dict]] = None  # For list/choice dialogs
    default_value: Optional[str] = None  # For input dialogs
    width_ratio: float = 0.6  # Ratio of screen width (0.0 to 1.0)
    height_ratio: float = 0.7  # Ratio of screen height (0.0 to 1.0)
    min_width: int = 40  # Minimum dialog width
    min_height: int = 15  # Minimum dialog height


class IUIBackend(ABC):
    """
    Abstract interface for UI backends.
    
    This interface defines all methods that a UI backend (TUI or GUI) must
    implement to work with TFM's business logic. Both curses and Qt backends
    will implement this interface.
    """
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the UI backend.
        
        This method should set up the UI environment (e.g., initialize curses,
        create Qt windows, set up colors, etc.).
        
        Returns:
            True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """
        Clean up UI resources.
        
        This method should release all UI resources and restore the terminal/
        display to its original state.
        """
        pass
    
    @abstractmethod
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Get current screen/window dimensions.
        
        Returns:
            Tuple of (height, width) in characters/pixels
        """
        pass
    
    @abstractmethod
    def render_panes(self, left_pane: Dict, right_pane: Dict, 
                    active_pane: str, layout: LayoutInfo):
        """
        Render the dual-pane file browser.
        
        Args:
            left_pane: Left pane data (path, files, selection, etc.)
            right_pane: Right pane data (path, files, selection, etc.)
            active_pane: Which pane is active ('left' or 'right')
            layout: Layout information for positioning
        """
        pass
    
    @abstractmethod
    def render_header(self, left_path: str, right_path: str, active_pane: str):
        """
        Render the header with directory paths.
        
        Args:
            left_path: Path displayed in left pane header
            right_path: Path displayed in right pane header
            active_pane: Which pane is active ('left' or 'right')
        """
        pass
    
    @abstractmethod
    def render_footer(self, left_info: str, right_info: str, active_pane: str):
        """
        Render the footer with file counts and sort info.
        
        Args:
            left_info: Information text for left pane footer
            right_info: Information text for right pane footer
            active_pane: Which pane is active ('left' or 'right')
        """
        pass
    
    @abstractmethod
    def render_status_bar(self, message: str, controls: List[Dict]):
        """
        Render the status bar with message and controls.
        
        Args:
            message: Status message to display
            controls: List of control hints (e.g., [{'key': 'F1', 'label': 'Help'}])
        """
        pass
    
    @abstractmethod
    def render_log_pane(self, messages: List[str], scroll_offset: int, 
                       height_ratio: float):
        """
        Render the log message pane.
        
        Args:
            messages: List of log messages to display
            scroll_offset: Scroll position in the message list
            height_ratio: Ratio of screen height to use for log pane
        """
        pass
    
    @abstractmethod
    def show_dialog(self, dialog_config: DialogConfig) -> Any:
        """
        Show a dialog and return user response.
        
        Args:
            dialog_config: Dialog configuration
        
        Returns:
            User response (type depends on dialog type):
            - confirmation: bool (True/False)
            - input: str or None
            - list: selected item(s) or None
            - info: None
            - progress: None (non-blocking)
        """
        pass
    
    @abstractmethod
    def show_progress(self, operation: str, current: int, total: int, 
                     message: str):
        """
        Show or update progress indicator for long operations.
        
        Args:
            operation: Name of the operation (e.g., 'Copying files')
            current: Current progress value
            total: Total progress value
            message: Current status message (e.g., current file name)
        """
        pass
    
    @abstractmethod
    def get_input_event(self, timeout: int = -1) -> Optional[InputEvent]:
        """
        Get next input event (key press, mouse click, etc.).
        
        Args:
            timeout: Timeout in milliseconds (-1 for blocking, 0 for non-blocking)
        
        Returns:
            InputEvent if available, None if timeout or no event
        """
        pass
    
    @abstractmethod
    def refresh(self):
        """
        Refresh the display.
        
        This method should update the screen/window to show all pending changes.
        """
        pass
    
    @abstractmethod
    def set_color_scheme(self, scheme: str):
        """
        Set the color scheme.
        
        Args:
            scheme: Color scheme name (e.g., 'dark', 'light', 'custom')
        """
        pass
