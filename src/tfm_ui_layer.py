"""
UI Layer Stack System for TFM

This module provides a dynamic stack-based architecture for managing UI components
in the TFM file manager. It replaces complex if-elif chains with a clean layer-based
approach where layers are managed in a stack structure with proper event routing and
intelligent rendering optimization.

Key Components:
- UILayer: Abstract base class defining the interface for all UI layers
- UILayerStack: Manages the stack of UI layers with event routing and rendering

The stack maintains layers in LIFO order with the FileManager main screen as the
permanent bottom layer. Events are routed to the top layer first, with propagation
to lower layers if not consumed. Rendering is optimized by skipping layers obscured
by full-screen layers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class UILayer(ABC):
    """
    Abstract base class for UI layers in the layer stack.
    
    All UI components that participate in the layer stack must implement
    this interface to handle events, rendering, and lifecycle management.
    
    The UILayer interface defines the contract for:
    - Event handling (keyboard and character events)
    - Rendering with dirty tracking
    - Full-screen layer detection
    - Lifecycle management (activation/deactivation)
    - Close request signaling
    """
    
    @abstractmethod
    def handle_key_event(self, event) -> bool:
        """
        Handle a key event.
        
        This method is called when a keyboard event occurs. The layer should
        process the event and return True if it consumed the event, or False
        to allow propagation to the next layer below.
        
        Args:
            event: KeyEvent to handle (from TTK backend)
        
        Returns:
            True if the event was consumed, False to propagate to next layer
        """
        pass
    
    @abstractmethod
    def handle_char_event(self, event) -> bool:
        """
        Handle a character event.
        
        This method is called when a character input event occurs (typically
        for text input). The layer should process the event and return True
        if it consumed the event, or False to allow propagation to the next
        layer below.
        
        Args:
            event: CharEvent to handle (from TTK backend)
        
        Returns:
            True if the event was consumed, False to propagate to next layer
        """
        pass
    
    @abstractmethod
    def render(self, renderer) -> None:
        """
        Render the layer's content.
        
        This method is called when the layer needs to be drawn. The layer
        should use the provided renderer to draw its content to the screen.
        
        Args:
            renderer: TTK renderer instance for drawing
        """
        pass
    
    @abstractmethod
    def is_full_screen(self) -> bool:
        """
        Query if this layer occupies the full screen.
        
        Full-screen layers obscure all layers below them, enabling
        rendering optimizations. The layer stack will skip rendering
        layers below the topmost full-screen layer.
        
        Returns:
            True if this layer is full-screen, False otherwise
        """
        pass
    
    @abstractmethod
    def needs_redraw(self) -> bool:
        """
        Query if this layer has dirty content that needs redrawing.
        
        The layer stack uses this to optimize rendering by only redrawing
        layers that have changed. A layer should return True if:
        - Its content has changed since last render
        - It needs to redraw due to a lower layer redrawing
        
        Returns:
            True if the layer needs redrawing, False otherwise
        """
        pass
    
    @abstractmethod
    def mark_dirty(self) -> None:
        """
        Mark this layer as needing a redraw.
        
        Called by the layer itself when its content changes, or by the
        layer stack when a lower layer has been redrawn (since layers
        above must redraw to maintain visual correctness).
        """
        pass
    
    @abstractmethod
    def clear_dirty(self) -> None:
        """
        Clear the dirty flag after rendering.
        
        Called by the layer stack after successfully rendering this layer.
        The layer should reset its internal dirty state.
        """
        pass
    
    @abstractmethod
    def should_close(self) -> bool:
        """
        Query if this layer wants to close.
        
        The layer stack checks this after event handling to determine
        if the layer should be popped from the stack. Layers signal
        they want to close by returning True from this method.
        
        Returns:
            True if the layer should be closed, False otherwise
        """
        pass
    
    @abstractmethod
    def on_activate(self) -> None:
        """
        Called when this layer becomes the top layer.
        
        This lifecycle method is invoked when:
        - The layer is pushed onto the stack
        - The layer above is popped, making this the new top layer
        
        Use this to initialize state, show cursor, mark dirty for
        initial render, etc.
        """
        pass
    
    @abstractmethod
    def on_deactivate(self) -> None:
        """
        Called when this layer is no longer the top layer.
        
        This lifecycle method is invoked when:
        - A new layer is pushed on top of this layer
        - This layer is popped from the stack
        
        Use this to clean up state, hide cursor, etc.
        """
        pass


class UILayerStack:
    """
    Manages a stack of UI layers with event routing and rendering coordination.
    
    The stack maintains layers in LIFO order, with the FileManager main screen
    as the permanent bottom layer. Events are routed to the top layer first,
    with propagation to lower layers if not consumed. Rendering is optimized
    by skipping layers obscured by full-screen layers.
    
    Key Features:
    - LIFO stack ordering with bottom layer protection
    - Event routing with propagation chain
    - Intelligent dirty tracking for rendering optimization
    - Full-screen layer optimization (skip rendering obscured layers)
    - Exception handling for robustness
    - Lifecycle management (activation/deactivation callbacks)
    
    Attributes:
        _layers: List of layers in the stack (index 0 = bottom)
        _log_manager: Optional LogManager for error logging
    """
    
    def __init__(self, bottom_layer: UILayer, log_manager=None):
        """
        Initialize the layer stack with a bottom layer.
        
        The bottom layer is the permanent base of the stack (typically the
        FileManager main screen) and cannot be removed.
        
        Args:
            bottom_layer: The permanent bottom layer (FileManager main screen)
            log_manager: Optional LogManager for error logging
        """
        self._layers: List[UILayer] = [bottom_layer]
        self._log_manager = log_manager
        
        # Activate the bottom layer
        bottom_layer.on_activate()
    
    def push(self, layer: UILayer) -> None:
        """
        Push a new layer onto the top of the stack.
        
        The previous top layer is deactivated, and the new layer is activated.
        This implements the lifecycle management for layer transitions.
        
        Args:
            layer: Layer to push onto the stack
        """
        # Deactivate current top layer
        if self._layers:
            self._layers[-1].on_deactivate()
        
        # Push new layer and activate it
        self._layers.append(layer)
        layer.on_activate()
    
    def pop(self) -> Optional[UILayer]:
        """
        Pop the top layer from the stack.
        
        The bottom layer cannot be popped. After popping, the new top layer
        is activated. This implements the lifecycle management for layer
        transitions.
        
        Returns:
            The popped layer, or None if the operation was rejected
        """
        # Prevent removal of bottom layer
        if len(self._layers) <= 1:
            if self._log_manager:
                self._log_manager.add_message("WARNING", "Cannot remove bottom layer from UI stack")
            return None
        
        # Pop top layer and deactivate it
        layer = self._layers.pop()
        layer.on_deactivate()
        
        # Activate new top layer
        if self._layers:
            self._layers[-1].on_activate()
        
        return layer
    
    def get_top_layer(self) -> UILayer:
        """
        Get the current top layer.
        
        Returns:
            The top layer in the stack
        """
        return self._layers[-1]
    
    def get_layer_count(self) -> int:
        """
        Get the number of layers in the stack.
        
        Returns:
            Number of layers (always >= 1 due to bottom layer)
        """
        return len(self._layers)
    
    def handle_key_event(self, event) -> bool:
        """
        Route a key event to layers, starting from the top.
        
        Events are routed to the top layer first. If the top layer consumes
        the event (returns True), propagation stops. Otherwise, the event
        is propagated to the next layer below, continuing until a layer
        consumes it or the bottom layer is reached.
        
        Exception handling: If a layer raises an exception during event
        handling, the exception is caught, logged, and propagation continues
        to the next layer.
        
        Args:
            event: KeyEvent to route
        
        Returns:
            True if any layer consumed the event, False otherwise
        """
        # Iterate from top to bottom
        for layer in reversed(self._layers):
            try:
                if layer.handle_key_event(event):
                    return True
            except Exception as e:
                if self._log_manager:
                    self._log_manager.add_message(
                        "ERROR",
                        f"Layer {layer.__class__.__name__} raised exception during key event: {e}"
                    )
                # Continue to next layer despite error
        
        return False
    
    def handle_char_event(self, event) -> bool:
        """
        Route a character event to layers, starting from the top.
        
        Events are routed to the top layer first. If the top layer consumes
        the event (returns True), propagation stops. Otherwise, the event
        is propagated to the next layer below, continuing until a layer
        consumes it or the bottom layer is reached.
        
        Exception handling: If a layer raises an exception during event
        handling, the exception is caught, logged, and propagation continues
        to the next layer.
        
        Args:
            event: CharEvent to route
        
        Returns:
            True if any layer consumed the event, False otherwise
        """
        # Iterate from top to bottom
        for layer in reversed(self._layers):
            try:
                if layer.handle_char_event(event):
                    return True
            except Exception as e:
                if self._log_manager:
                    self._log_manager.add_message(
                        "ERROR",
                        f"Layer {layer.__class__.__name__} raised exception during char event: {e}"
                    )
                # Continue to next layer despite error
        
        return False
    
    def render(self, renderer) -> None:
        """
        Render visible layers with intelligent dirty tracking.
        
        This method implements the core rendering optimization strategy:
        1. Find the topmost full-screen layer (if any)
        2. Find the lowest dirty layer at or above the topmost full-screen layer
        3. Mark all layers above the lowest dirty layer as dirty
        4. Render from the lowest dirty layer upward
        5. Clear dirty flags after successful rendering
        6. Refresh the screen
        
        Only renders layers that have dirty content or are above a dirty layer.
        Layers below the topmost full-screen layer are skipped for performance.
        
        Exception handling: If a layer raises an exception during rendering,
        the exception is caught, logged, and rendering continues with other
        layers.
        
        Args:
            renderer: TTK renderer instance for drawing
        """
        # Find topmost full-screen layer
        topmost_fullscreen_index = 0
        for i in range(len(self._layers) - 1, -1, -1):
            if self._layers[i].is_full_screen():
                topmost_fullscreen_index = i
                break
        
        # Find lowest dirty layer at or above the topmost full-screen layer
        lowest_dirty_index = None
        for i in range(topmost_fullscreen_index, len(self._layers)):
            if self._layers[i].needs_redraw():
                lowest_dirty_index = i
                break
        
        # If no dirty layers, nothing to render
        if lowest_dirty_index is None:
            return
        
        # Mark all layers above the lowest dirty layer as dirty
        # (they need to redraw because a lower layer changed)
        for i in range(lowest_dirty_index + 1, len(self._layers)):
            self._layers[i].mark_dirty()
        
        # Render from lowest dirty layer to top
        for i in range(lowest_dirty_index, len(self._layers)):
            layer = self._layers[i]
            if layer.needs_redraw():
                try:
                    layer.render(renderer)
                    layer.clear_dirty()
                except Exception as e:
                    if self._log_manager:
                        self._log_manager.add_message(
                            "ERROR",
                            f"Layer {layer.__class__.__name__} raised exception during rendering: {e}"
                        )
                    # Continue rendering other layers despite error
        
        # Refresh screen after rendering
        renderer.refresh()
    
    def check_and_close_top_layer(self) -> bool:
        """
        Check if the top layer wants to close and pop it if so.
        
        This method should be called after event handling to allow layers
        to signal they want to close (e.g., user pressed ESC in a dialog).
        
        Returns:
            True if a layer was closed, False otherwise
        """
        top_layer = self.get_top_layer()
        if top_layer.should_close():
            self.pop()
            return True
        return False


class FileManagerLayer(UILayer):
    """
    Layer wrapper for the FileManager main screen.
    
    This is the permanent bottom layer that handles file browsing,
    selection, and main application commands. It wraps the existing
    FileManager functionality to integrate with the layer stack system.
    
    The FileManagerLayer delegates event handling and rendering to the
    FileManager instance, while managing its own dirty state for rendering
    optimization.
    
    Attributes:
        file_manager: The FileManager instance to wrap
        _close_requested: Flag indicating if application quit was requested
        _dirty: Flag indicating if layer needs redrawing
    """
    
    def __init__(self, file_manager):
        """
        Initialize the FileManagerLayer wrapper.
        
        Args:
            file_manager: The FileManager instance to wrap
        """
        self.file_manager = file_manager
        self._close_requested = False
        self._dirty = True  # Start dirty to ensure initial render
    
    def handle_key_event(self, event) -> bool:
        """
        Handle a key event for the main FileManager screen.
        
        This method delegates to the FileManager's handle_main_screen_key_event method,
        which processes all main screen keyboard events including navigation,
        selection, commands, and shortcuts.
        
        Args:
            event: KeyEvent to handle
        
        Returns:
            True if the event was consumed, False otherwise
        """
        # Delegate to FileManager's main screen key handling logic
        result = self.file_manager.handle_main_screen_key_event(event)
        
        # Mark dirty if event was consumed (content likely changed)
        if result:
            self._dirty = True
        
        return result
    
    def handle_char_event(self, event) -> bool:
        """
        Handle a character event.
        
        The FileManager main screen doesn't handle character events directly
        (no text input on main screen), so this always returns False to allow
        propagation.
        
        Args:
            event: CharEvent to handle
        
        Returns:
            False (main screen doesn't handle char events)
        """
        # FileManager main screen doesn't handle char events
        # (no text input on main screen)
        return False
    
    def render(self, renderer) -> None:
        """
        Render the FileManager main screen.
        
        This method renders the complete main screen including header, file panes,
        log pane, and status bar. It only performs a full redraw when needed.
        
        Args:
            renderer: TTK renderer instance for drawing
        """
        # Only do full redraw when needed
        if self.needs_redraw():
            self.file_manager.refresh_files()
            
            # Clear screen with proper background
            self.file_manager.clear_screen_with_background()
            
            # Draw interface components
            self.file_manager.draw_header()
            self.file_manager.draw_files()
            self.file_manager.draw_log_pane()
            self.file_manager.draw_status()
            
            # Note: Don't call renderer.refresh() here - UILayerStack will do it
    
    def is_full_screen(self) -> bool:
        """
        Query if this layer occupies the full screen.
        
        The FileManager main screen always occupies the full terminal screen.
        
        Returns:
            True (main screen is always full-screen)
        """
        return True  # Main screen occupies full screen
    
    def needs_redraw(self) -> bool:
        """
        Query if this layer needs redrawing.
        
        The layer needs redrawing if either:
        - Its internal dirty flag is set
        - The FileManager's needs_full_redraw flag is set
        
        Returns:
            True if the layer needs redrawing, False otherwise
        """
        return self._dirty or self.file_manager.needs_full_redraw
    
    def mark_dirty(self) -> None:
        """
        Mark this layer as needing a redraw.
        
        This is called by the layer stack when a lower layer has been redrawn,
        or by the layer itself when its content changes.
        """
        self._dirty = True
    
    def clear_dirty(self) -> None:
        """
        Clear the dirty flag after rendering.
        
        This is called by the layer stack after successfully rendering this
        layer. It clears both the layer's internal dirty flag and the
        FileManager's needs_full_redraw flag.
        """
        self._dirty = False
        self.file_manager.needs_full_redraw = False
    
    def should_close(self) -> bool:
        """
        Query if this layer wants to close.
        
        The FileManagerLayer signals it wants to close when the user has
        requested to quit the application (e.g., by pressing 'q' and
        confirming the quit dialog).
        
        Returns:
            True if application quit was requested, False otherwise
        """
        return self._close_requested
    
    def request_close(self):
        """
        Request that the application quit.
        
        This method is called when the user confirms they want to quit the
        application. It sets the close request flag, which will be detected
        by the layer stack and cause the application to exit.
        """
        self._close_requested = True
    
    def on_activate(self) -> None:
        """
        Called when this layer becomes the top layer.
        
        The FileManager main screen is typically always active as the bottom
        layer, so no special activation is needed. However, if it becomes
        the top layer again after a dialog/viewer is closed, we mark it
        dirty to ensure it's redrawn.
        """
        # Main screen is always active, but mark dirty to ensure redraw
        # when it becomes the top layer again
        self._dirty = True
    
    def on_deactivate(self) -> None:
        """
        Called when this layer is no longer the top layer.
        
        The FileManager main screen remains active even when covered by
        dialogs or viewers, so no special deactivation is needed.
        """
        # Main screen remains active even when covered by dialogs
        pass
