"""
UI Layer Stack System for TFM

This module provides a dynamic stack-based architecture for managing UI components
in the TFM file manager. It replaces complex if-elif chains with a clean layer-based
approach where layers are managed in a stack structure with intelligent rendering
optimization.

Key Components:
- UILayer: Abstract base class defining the interface for all UI layers
- UILayerStack: Manages the stack of UI layers with event routing and rendering

The stack maintains layers in LIFO order with the FileManager main screen as the
permanent bottom layer. Events are routed ONLY to the top layer - there is no
event propagation to lower layers. Rendering is optimized by skipping layers
obscured by full-screen layers.
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
        
        This method is called when a keyboard event occurs and this layer is
        the top layer in the stack. The layer should process the event and
        return True if it consumed the event, or False if it did not handle it.
        
        Note: Events are only sent to the top layer. Lower layers do not
        receive events unless they become the top layer.
        
        Args:
            event: KeyEvent to handle (from TTK backend)
        
        Returns:
            True if the event was consumed, False otherwise
        """
        pass
    
    @abstractmethod
    def handle_char_event(self, event) -> bool:
        """
        Handle a character event.
        
        This method is called when a character input event occurs (typically
        for text input) and this layer is the top layer in the stack. The
        layer should process the event and return True if it consumed the
        event, or False if it did not handle it.
        
        Note: Events are only sent to the top layer. Lower layers do not
        receive events unless they become the top layer.
        
        Args:
            event: CharEvent to handle (from TTK backend)
        
        Returns:
            True if the event was consumed, False otherwise
        """
        pass
    
    @abstractmethod
    def handle_system_event(self, event) -> bool:
        """
        Handle a system event (resize, close, etc.).
        
        This method is called when a system event occurs. Unlike key and
        character events which only go to the top layer, system events are
        BROADCAST to ALL layers in the stack. This allows all layers to
        update their internal state when system-wide changes occur.
        
        Common system events:
        - Window resize: All layers should mark themselves dirty and may need
          to recalculate layout based on new dimensions
        - Window close: Layers can perform cleanup or cancel operations
        
        Args:
            event: SystemEvent to handle (from TTK backend)
        
        Returns:
            True if the event was consumed, False otherwise
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
    as the permanent bottom layer. Events are routed ONLY to the top layer -
    there is no event propagation to lower layers. Rendering is optimized
    by skipping layers obscured by full-screen layers.
    
    Key Features:
    - LIFO stack ordering with bottom layer protection
    - Top-layer-only event routing (no propagation)
    - Intelligent dirty tracking for rendering optimization
    - Full-screen layer optimization (skip rendering obscured layers)
    - Exception handling for robustness
    - Lifecycle management (activation/deactivation callbacks)
    - Adaptive FPS integration (marks activity on rendering)
    
    Attributes:
        _layers: List of layers in the stack (index 0 = bottom)
        _log_manager: Optional LogManager for error logging
        _adaptive_fps: Optional AdaptiveFPSManager for CPU optimization
    """
    
    def __init__(self, bottom_layer: UILayer, log_manager=None, adaptive_fps=None):
        """
        Initialize the layer stack with a bottom layer.
        
        The bottom layer is the permanent base of the stack (typically the
        FileManager main screen) and cannot be removed.
        
        Args:
            bottom_layer: The permanent bottom layer (FileManager main screen)
            log_manager: Optional LogManager for error logging
            adaptive_fps: Optional AdaptiveFPSManager for CPU optimization
        """
        self._layers: List[UILayer] = [bottom_layer]
        self._log_manager = log_manager
        self._adaptive_fps = adaptive_fps
        
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
        Route a key event to the top layer only.
        
        Events are only sent to the top layer. The top layer is responsible
        for handling the event completely. Event propagation to lower layers
        is not supported - only the topmost layer receives events.
        
        Exception handling: If the top layer raises an exception during event
        handling, the exception is caught and logged.
        
        Args:
            event: KeyEvent to route
        
        Returns:
            True if the top layer consumed the event, False otherwise
        """
        # Only route to the top layer
        top_layer = self._layers[-1]
        try:
            return top_layer.handle_key_event(event)
        except Exception as e:
            if self._log_manager:
                self._log_manager.add_message(
                    "ERROR",
                    f"Layer {top_layer.__class__.__name__} raised exception during key event: {e}"
                )
            return False
    
    def handle_char_event(self, event) -> bool:
        """
        Route a character event to the top layer only.
        
        Events are only sent to the top layer. The top layer is responsible
        for handling the event completely. Event propagation to lower layers
        is not supported - only the topmost layer receives events.
        
        Exception handling: If the top layer raises an exception during event
        handling, the exception is caught and logged.
        
        Args:
            event: CharEvent to route
        
        Returns:
            True if the top layer consumed the event, False otherwise
        """
        # Only route to the top layer
        top_layer = self._layers[-1]
        try:
            return top_layer.handle_char_event(event)
        except Exception as e:
            if self._log_manager:
                self._log_manager.add_message(
                    "ERROR",
                    f"Layer {top_layer.__class__.__name__} raised exception during char event: {e}"
                )
            return False
    
    def handle_system_event(self, event) -> bool:
        """
        Broadcast a system event to all layers in the stack.
        
        System events (resize, close, etc.) are broadcast to ALL layers in the
        stack, not just the top layer. This allows all layers to update their
        internal state when system-wide changes occur (e.g., window resize).
        
        Unlike key and character events which only go to the top layer, system
        events affect the entire application state and all layers need to know
        about them.
        
        Exception handling: If any layer raises an exception during event
        handling, the exception is caught and logged, but broadcasting continues
        to other layers.
        
        Args:
            event: SystemEvent to broadcast
        
        Returns:
            True if at least one layer consumed the event, False otherwise
        """
        any_handled = False
        
        # Broadcast to all layers (bottom to top)
        for layer in self._layers:
            try:
                if layer.handle_system_event(event):
                    any_handled = True
            except Exception as e:
                if self._log_manager:
                    self._log_manager.add_message(
                        "ERROR",
                        f"Layer {layer.__class__.__name__} raised exception during system event: {e}"
                    )
                # Continue broadcasting to other layers despite error
        
        return any_handled
    
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
        7. Mark activity for adaptive FPS (rendering indicates UI changes)
        
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
        
        # Mark activity for adaptive FPS since we're about to render
        if self._adaptive_fps:
            self._adaptive_fps.mark_activity()
        
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
