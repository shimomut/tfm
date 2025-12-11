#!/usr/bin/env python3
"""
TTK Test Interface

This module provides a comprehensive test interface for the TTK library,
demonstrating text rendering with various colors and attributes, rectangle
and line drawing, input handling, and window dimension display.

The test interface validates that rendering backends work correctly and
produce equivalent output across different platforms.
"""

from typing import Optional
from ttk.renderer import Renderer, TextAttribute
from ttk.input_event import InputEvent, KeyCode
from ttk.demo.performance import PerformanceMonitor


class TestInterface:
    """
    Test interface for demonstrating TTK rendering capabilities.
    
    This class provides a comprehensive UI that tests:
    - Text rendering with various colors and attributes
    - Rectangle and line drawing
    - Input event handling and echo
    - Window dimension and coordinate system display
    """
    
    def __init__(self, renderer: Renderer, enable_performance_monitoring: bool = True):
        """
        Initialize the test interface.
        
        Args:
            renderer: The rendering backend to use for display
            enable_performance_monitoring: Whether to enable performance monitoring
        """
        self.renderer = renderer
        self.running = False
        self.last_input = None
        self.input_history = []
        self.max_history = 5
        
        # Performance monitoring
        self.enable_performance_monitoring = enable_performance_monitoring
        self.performance_monitor = PerformanceMonitor() if enable_performance_monitoring else None
        
    def initialize_colors(self):
        """Initialize color pairs for the test interface."""
        # Color pair 1: White on black (default)
        self.renderer.init_color_pair(1, (255, 255, 255), (0, 0, 0))
        
        # Color pair 2: Red on black
        self.renderer.init_color_pair(2, (255, 0, 0), (0, 0, 0))
        
        # Color pair 3: Green on black
        self.renderer.init_color_pair(3, (0, 255, 0), (0, 0, 0))
        
        # Color pair 4: Blue on black
        self.renderer.init_color_pair(4, (0, 0, 255), (0, 0, 0))
        
        # Color pair 5: Yellow on black
        self.renderer.init_color_pair(5, (255, 255, 0), (0, 0, 0))
        
        # Color pair 6: Cyan on black
        self.renderer.init_color_pair(6, (0, 255, 255), (0, 0, 0))
        
        # Color pair 7: Magenta on black
        self.renderer.init_color_pair(7, (255, 0, 255), (0, 0, 0))
        
        # Color pair 8: White on blue (for headers)
        self.renderer.init_color_pair(8, (255, 255, 255), (0, 0, 128))
        
        # Color pair 9: Black on white (for input echo)
        self.renderer.init_color_pair(9, (0, 0, 0), (255, 255, 255))
        
        # Color pair 10: Gray on black
        self.renderer.init_color_pair(10, (128, 128, 128), (0, 0, 0))
    
    def draw_header(self, row: int):
        """
        Draw the header section with title and instructions.
        
        Args:
            row: Starting row for the header
            
        Returns:
            Next available row after the header
        """
        rows, cols = self.renderer.get_dimensions()
        
        # Draw title bar
        title = "TTK Test Interface"
        title_x = (cols - len(title)) // 2
        self.renderer.draw_text(row, 0, " " * cols, 8)
        self.renderer.draw_text(row, title_x, title, 8, TextAttribute.BOLD)
        
        # Draw instructions
        row += 2
        self.renderer.draw_text(row, 0, "Press 'q' to quit, any other key to test input", 10)
        
        return row + 2
    
    def draw_color_test(self, row: int):
        """
        Draw color test section showing various colors.
        
        Args:
            row: Starting row for the color test
            
        Returns:
            Next available row after the color test
        """
        self.renderer.draw_text(row, 0, "Color Test:", 1, TextAttribute.BOLD)
        row += 1
        
        # Test basic colors
        colors = [
            (1, "White"),
            (2, "Red"),
            (3, "Green"),
            (4, "Blue"),
            (5, "Yellow"),
            (6, "Cyan"),
            (7, "Magenta"),
        ]
        
        for color_pair, name in colors:
            self.renderer.draw_text(row, 2, f"{name:8s}", color_pair)
            row += 1
        
        return row + 1
    
    def draw_attribute_test(self, row: int):
        """
        Draw text attribute test section.
        
        Args:
            row: Starting row for the attribute test
            
        Returns:
            Next available row after the attribute test
        """
        self.renderer.draw_text(row, 0, "Text Attributes:", 1, TextAttribute.BOLD)
        row += 1
        
        # Test individual attributes
        self.renderer.draw_text(row, 2, "Normal text", 1, TextAttribute.NORMAL)
        row += 1
        
        self.renderer.draw_text(row, 2, "Bold text", 1, TextAttribute.BOLD)
        row += 1
        
        self.renderer.draw_text(row, 2, "Underline text", 1, TextAttribute.UNDERLINE)
        row += 1
        
        self.renderer.draw_text(row, 2, "Reverse text", 1, TextAttribute.REVERSE)
        row += 1
        
        # Test combined attributes
        self.renderer.draw_text(
            row, 2, "Bold + Underline", 1,
            TextAttribute.BOLD | TextAttribute.UNDERLINE
        )
        row += 1
        
        self.renderer.draw_text(
            row, 2, "Bold + Reverse", 2,
            TextAttribute.BOLD | TextAttribute.REVERSE
        )
        row += 1
        
        return row + 1
    
    def draw_shape_test(self, row: int):
        """
        Draw shape test section with rectangles and lines.
        
        Args:
            row: Starting row for the shape test
            
        Returns:
            Next available row after the shape test
        """
        rows, cols = self.renderer.get_dimensions()
        
        self.renderer.draw_text(row, 0, "Shape Test:", 1, TextAttribute.BOLD)
        row += 1
        
        # Draw outlined rectangle
        if row + 5 < rows and cols >= 30:
            self.renderer.draw_text(row, 2, "Outlined rectangle:", 10)
            self.renderer.draw_rect(row + 1, 2, 4, 20, 3, filled=False)
            row += 5
        
        # Draw filled rectangle
        if row + 5 < rows and cols >= 30:
            self.renderer.draw_text(row, 2, "Filled rectangle:", 10)
            self.renderer.draw_rect(row + 1, 2, 3, 15, 4, filled=True)
            row += 5
        
        # Draw horizontal line
        if row + 2 < rows and cols >= 30:
            self.renderer.draw_text(row, 2, "Horizontal line:", 10)
            self.renderer.draw_hline(row + 1, 2, '-', 25, 5)
            row += 3
        
        # Draw vertical line
        if row + 6 < rows and cols >= 30:
            self.renderer.draw_text(row, 2, "Vertical line:", 10)
            self.renderer.draw_vline(row + 1, 2, '|', 5, 6)
            row += 7
        
        return row
    
    def draw_coordinate_info(self, row: int):
        """
        Draw coordinate system and window dimension information.
        
        Args:
            row: Starting row for the coordinate info
            
        Returns:
            Next available row after the coordinate info
        """
        rows, cols = self.renderer.get_dimensions()
        
        self.renderer.draw_text(row, 0, "Window Information:", 1, TextAttribute.BOLD)
        row += 1
        
        self.renderer.draw_text(row, 2, f"Dimensions: {rows} rows x {cols} columns", 1)
        row += 1
        
        self.renderer.draw_text(row, 2, "Coordinate system: (0,0) at top-left", 1)
        row += 1
        
        self.renderer.draw_text(row, 2, f"Bottom-right: ({rows-1},{cols-1})", 1)
        row += 1
        
        # Draw corner markers
        if rows > 2 and cols > 2:
            self.renderer.draw_text(0, 0, "+", 2)  # Top-left
            self.renderer.draw_text(0, cols - 1, "+", 2)  # Top-right
            self.renderer.draw_text(rows - 1, 0, "+", 2)  # Bottom-left
            self.renderer.draw_text(rows - 1, cols - 1, "+", 2)  # Bottom-right
        
        return row + 1
    
    def draw_performance_metrics(self, row: int):
        """
        Draw performance metrics section.
        
        Args:
            row: Starting row for the performance metrics
            
        Returns:
            Next available row after the performance metrics
        """
        rows, cols = self.renderer.get_dimensions()
        
        # Check if we have enough space and performance monitoring is enabled
        if row + 6 >= rows or not self.enable_performance_monitoring:
            return row
        
        self.renderer.draw_text(row, 0, "Performance Metrics:", 1, TextAttribute.BOLD)
        row += 1
        
        # Get performance metrics
        metrics = self.performance_monitor.get_summary()
        
        # Display FPS
        fps_str = f"FPS: {metrics['fps']:.1f} (avg: {metrics['average_fps']:.1f})"
        self.renderer.draw_text(row, 2, fps_str, 3)
        row += 1
        
        # Display render time
        render_str = f"Render time: {metrics['render_time_ms']:.2f}ms"
        self.renderer.draw_text(row, 2, render_str, 5)
        row += 1
        
        # Display min/max render time
        minmax_str = f"  Min: {metrics['min_render_time_ms']:.2f}ms  Max: {metrics['max_render_time_ms']:.2f}ms"
        self.renderer.draw_text(row, 2, minmax_str, 10)
        row += 1
        
        # Display frame time
        frame_str = f"Frame time: {metrics['frame_time_ms']:.2f}ms"
        self.renderer.draw_text(row, 2, frame_str, 6)
        row += 1
        
        # Display total frames and uptime
        stats_str = f"Frames: {metrics['total_frames']}  Uptime: {metrics['uptime']:.1f}s"
        self.renderer.draw_text(row, 2, stats_str, 10)
        row += 1
        
        return row + 1
    
    def draw_input_echo(self, row: int):
        """
        Draw input echo area showing recent key presses.
        
        Args:
            row: Starting row for the input echo area
            
        Returns:
            Next available row after the input echo area
        """
        rows, cols = self.renderer.get_dimensions()
        
        # Check if we have enough space
        if row + 8 >= rows:
            return row
        
        self.renderer.draw_text(row, 0, "Input Echo:", 1, TextAttribute.BOLD)
        row += 1
        
        # Draw current input
        if self.last_input:
            self.renderer.draw_text(row, 2, "Last key:", 10)
            
            # Format the input information
            if self.last_input.is_printable():
                key_str = f"'{self.last_input.char}' (code: {self.last_input.key_code})"
            elif self.last_input.is_special_key():
                key_str = f"Special key (code: {self.last_input.key_code})"
            else:
                key_str = f"Key code: {self.last_input.key_code}"
            
            # Show modifiers if any
            modifiers = []
            if self.last_input.modifiers:
                from ttk.input_event import ModifierKey
                if self.last_input.has_modifier(ModifierKey.SHIFT):
                    modifiers.append("Shift")
                if self.last_input.has_modifier(ModifierKey.CONTROL):
                    modifiers.append("Ctrl")
                if self.last_input.has_modifier(ModifierKey.ALT):
                    modifiers.append("Alt")
                if self.last_input.has_modifier(ModifierKey.COMMAND):
                    modifiers.append("Cmd")
            
            modifier_str = " + ".join(modifiers) if modifiers else "None"
            
            self.renderer.draw_text(row, 12, key_str, 9)
            row += 1
            self.renderer.draw_text(row, 2, f"Modifiers: {modifier_str}", 10)
            row += 1
        else:
            self.renderer.draw_text(row, 2, "No input yet", 10)
            row += 1
        
        # Draw input history
        row += 1
        self.renderer.draw_text(row, 2, "Recent inputs:", 10)
        row += 1
        
        for i, event in enumerate(self.input_history[-self.max_history:]):
            if event.is_printable():
                display = f"'{event.char}'"
            elif event.is_special_key():
                display = f"<{event.key_code}>"
            else:
                display = f"[{event.key_code}]"
            
            self.renderer.draw_text(row + i, 4, display, 10)
        
        return row + self.max_history
    
    def draw_interface(self):
        """Draw the complete test interface."""
        # Start performance monitoring for rendering
        if self.performance_monitor:
            self.performance_monitor.start_render()
        
        # Clear the screen
        self.renderer.clear()
        
        # Draw all sections
        row = 0
        row = self.draw_header(row)
        
        # Get dimensions to check available space
        rows, cols = self.renderer.get_dimensions()
        
        # Draw sections if we have space
        if row < rows - 5:
            row = self.draw_color_test(row)
        
        if row < rows - 5:
            row = self.draw_attribute_test(row)
        
        if row < rows - 10:
            row = self.draw_shape_test(row)
        
        if row < rows - 5:
            row = self.draw_coordinate_info(row)
        
        if row < rows - 8:
            row = self.draw_performance_metrics(row)
        
        if row < rows - 8:
            row = self.draw_input_echo(row)
        
        # Refresh the display
        self.renderer.refresh()
        
        # End performance monitoring for rendering
        if self.performance_monitor:
            self.performance_monitor.end_render()
    
    def handle_input(self, event: InputEvent) -> bool:
        """
        Handle input events.
        
        Args:
            event: The input event to handle
            
        Returns:
            True to continue running, False to quit
        """
        # Handle resize events
        if event.key_code == KeyCode.RESIZE:
            # Window was resized - redraw interface with new dimensions
            # Don't store resize events in history
            return True
        
        # Store the input
        self.last_input = event
        self.input_history.append(event)
        
        # Keep history limited
        if len(self.input_history) > 20:
            self.input_history = self.input_history[-20:]
        
        # Check for quit command
        if event.char and event.char.lower() == 'q':
            return False
        
        # Check for ESC key
        if event.key_code == KeyCode.ESCAPE:
            return False
        
        return True
    
    def run(self):
        """
        Run the test interface main loop.
        
        This displays the test interface and handles user input until
        the user quits.
        """
        self.running = True
        
        try:
            # Initialize colors
            self.initialize_colors()
            
            # Draw initial interface
            if self.performance_monitor:
                self.performance_monitor.start_frame()
            self.draw_interface()
            
            # Main event loop
            while self.running:
                # Start frame timing
                if self.performance_monitor:
                    self.performance_monitor.start_frame()
                
                # Get input with timeout
                event = self.renderer.get_input(timeout_ms=100)
                
                if event is None:
                    # No input, but still redraw to update performance metrics
                    if self.performance_monitor:
                        self.draw_interface()
                    continue
                
                # Check for resize event first
                if event.key_code == KeyCode.RESIZE:
                    # Window was resized - redraw interface with new dimensions
                    self.draw_interface()
                    continue
                
                # Handle the input
                if not self.handle_input(event):
                    self.running = False
                    break
                
                # Redraw interface to show updated input
                self.draw_interface()
                
        except KeyboardInterrupt:
            # User interrupted with Ctrl+C
            self.running = False
        except Exception as e:
            # Log error and re-raise
            print(f"Error in test interface: {e}")
            raise
        finally:
            self.running = False


def create_test_interface(renderer: Renderer, enable_performance_monitoring: bool = True) -> TestInterface:
    """
    Factory function to create a test interface.
    
    Args:
        renderer: The rendering backend to use
        enable_performance_monitoring: Whether to enable performance monitoring
        
    Returns:
        Configured TestInterface instance
    """
    return TestInterface(renderer, enable_performance_monitoring)
