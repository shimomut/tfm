# TTK Examples

This document provides practical examples for common use cases with TTK.

## Table of Contents

- [Basic Applications](#basic-applications)
- [User Interface Components](#user-interface-components)
- [Input Handling](#input-handling)
- [Animation and Updates](#animation-and-updates)
- [File Operations](#file-operations)
- [Advanced Patterns](#advanced-patterns)

## Basic Applications

### Hello World

The simplest TTK application:

```python
from ttk.backends.curses_backend import CursesBackend
from ttk import KeyCode

renderer = CursesBackend()
renderer.initialize()

try:
    renderer.draw_text(0, 0, "Hello, World!")
    renderer.draw_text(1, 0, "Press any key to exit")
    renderer.refresh()
    renderer.get_input()
finally:
    renderer.shutdown()
```

### Application Template

A reusable application structure:

```python
from ttk.backends.curses_backend import CursesBackend
from ttk import KeyCode

class Application:
    def __init__(self):
        self.renderer = CursesBackend()
        self.running = False
    
    def initialize(self):
        """Initialize the application."""
        self.renderer.initialize()
        self.renderer.init_color_pair(1, (255, 255, 255), (0, 0, 128))
    
    def shutdown(self):
        """Clean up resources."""
        self.renderer.shutdown()
    
    def draw(self):
        """Draw the UI."""
        self.renderer.clear()
        self.renderer.draw_text(0, 0, "My Application", color_pair=1)
        self.renderer.refresh()
    
    def handle_input(self, event):
        """Handle input events."""
        if event.key_code == KeyCode.ESCAPE:
            self.running = False
    
    def run(self):
        """Main application loop."""
        self.initialize()
        try:
            self.running = True
            while self.running:
                self.draw()
                event = self.renderer.get_input()
                self.handle_input(event)
        finally:
            self.shutdown()

if __name__ == '__main__':
    app = Application()
    app.run()
```

## User Interface Components

### Status Bar

A status bar at the bottom of the screen:

```python
def draw_status_bar(renderer, message, color_pair=1):
    """Draw a status bar at the bottom."""
    rows, cols = renderer.get_dimensions()
    status_row = rows - 1
    
    # Pad or truncate message to fit
    if len(message) > cols:
        message = message[:cols]
    else:
        message = message.ljust(cols)
    
    renderer.draw_text(status_row, 0, message, color_pair=color_pair)

# Usage
renderer.init_color_pair(1, (0, 0, 0), (200, 200, 200))
draw_status_bar(renderer, "Ready | Press F1 for help", color_pair=1)
```

### Title Bar

A title bar at the top of the screen:

```python
from ttk import TextAttribute

def draw_title_bar(renderer, title, color_pair=1):
    """Draw a title bar at the top."""
    rows, cols = renderer.get_dimensions()
    
    # Center the title
    if len(title) > cols:
        title = title[:cols]
    else:
        title = title.center(cols)
    
    renderer.draw_text(0, 0, title, color_pair=color_pair,
                      attributes=TextAttribute.BOLD)

# Usage
renderer.init_color_pair(1, (255, 255, 255), (0, 0, 128))
draw_title_bar(renderer, "File Manager", color_pair=1)
```

### Menu System

A simple vertical menu:

```python
from ttk import KeyCode, TextAttribute

class Menu:
    def __init__(self, items):
        self.items = items
        self.selected = 0
    
    def draw(self, renderer, row, col):
        """Draw the menu."""
        for i, item in enumerate(self.items):
            if i == self.selected:
                # Highlight selected item
                renderer.draw_text(row + i, col, f"> {item}",
                                 attributes=TextAttribute.REVERSE)
            else:
                renderer.draw_text(row + i, col, f"  {item}")
    
    def handle_input(self, event):
        """Handle menu navigation."""
        if event.key_code == KeyCode.UP:
            self.selected = max(0, self.selected - 1)
        elif event.key_code == KeyCode.DOWN:
            self.selected = min(len(self.items) - 1, self.selected + 1)
        elif event.key_code == KeyCode.ENTER:
            return self.selected  # Return selected index
        return None

# Usage
menu = Menu(["New File", "Open File", "Save", "Exit"])

while True:
    renderer.clear()
    menu.draw(renderer, 2, 5)
    renderer.refresh()
    
    event = renderer.get_input()
    result = menu.handle_input(event)
    
    if result is not None:
        print(f"Selected: {menu.items[result]}")
        break
```

### Dialog Box

A centered dialog box:

```python
def draw_dialog(renderer, title, message, width=40):
    """Draw a centered dialog box."""
    rows, cols = renderer.get_dimensions()
    
    # Calculate dialog dimensions
    lines = message.split('\n')
    height = len(lines) + 4  # Title + message + padding
    
    # Center the dialog
    start_row = (rows - height) // 2
    start_col = (cols - width) // 2
    
    # Draw box
    renderer.draw_rect(start_row, start_col, height, width, filled=True)
    renderer.draw_rect(start_row, start_col, height, width, filled=False)
    
    # Draw title
    title_text = f" {title} ".center(width - 2)
    renderer.draw_text(start_row, start_col + 1, title_text,
                      attributes=TextAttribute.BOLD)
    
    # Draw message
    for i, line in enumerate(lines):
        line_text = line.center(width - 2)
        renderer.draw_text(start_row + 2 + i, start_col + 1, line_text)
    
    # Draw instruction
    instruction = "Press any key to continue".center(width - 2)
    renderer.draw_text(start_row + height - 2, start_col + 1, instruction)

# Usage
draw_dialog(renderer, "Information", "File saved successfully!")
renderer.refresh()
renderer.get_input()
```

### Progress Bar

An animated progress bar:

```python
def draw_progress_bar(renderer, row, col, width, progress, color_pair=1):
    """
    Draw a progress bar.
    
    Args:
        progress: Value from 0.0 to 1.0
    """
    filled_width = int(width * progress)
    empty_width = width - filled_width
    
    # Draw filled portion
    if filled_width > 0:
        renderer.draw_text(row, col, '█' * filled_width, color_pair=color_pair)
    
    # Draw empty portion
    if empty_width > 0:
        renderer.draw_text(row, col + filled_width, '░' * empty_width)
    
    # Draw percentage
    percent_text = f" {int(progress * 100)}% "
    percent_col = col + (width - len(percent_text)) // 2
    renderer.draw_text(row, percent_col, percent_text)

# Usage
import time

renderer.init_color_pair(1, (255, 255, 255), (0, 128, 0))

for i in range(101):
    renderer.clear()
    renderer.draw_text(5, 10, "Processing...")
    draw_progress_bar(renderer, 7, 10, 50, i / 100.0, color_pair=1)
    renderer.refresh()
    time.sleep(0.05)
```

## Input Handling

### Keyboard Shortcuts

Handle common keyboard shortcuts:

```python
from ttk import KeyCode, ModifierKey

def handle_shortcuts(event):
    """Handle keyboard shortcuts."""
    # Ctrl+C - Copy
    if event.char == 'c' and event.has_modifier(ModifierKey.CONTROL):
        print("Copy")
        return True
    
    # Ctrl+V - Paste
    if event.char == 'v' and event.has_modifier(ModifierKey.CONTROL):
        print("Paste")
        return True
    
    # Ctrl+S - Save
    if event.char == 's' and event.has_modifier(ModifierKey.CONTROL):
        print("Save")
        return True
    
    # Ctrl+Q - Quit
    if event.char == 'q' and event.has_modifier(ModifierKey.CONTROL):
        print("Quit")
        return False
    
    return True

# Usage
while True:
    event = renderer.get_input()
    if not handle_shortcuts(event):
        break
```

### Text Input

Simple text input field:

```python
from ttk import KeyCode

class TextInput:
    def __init__(self, max_length=50):
        self.text = ""
        self.max_length = max_length
        self.cursor_pos = 0
    
    def handle_input(self, event):
        """Handle text input."""
        if event.is_printable() and len(self.text) < self.max_length:
            # Insert character at cursor
            self.text = (self.text[:self.cursor_pos] + 
                        event.char + 
                        self.text[self.cursor_pos:])
            self.cursor_pos += 1
        
        elif event.key_code == KeyCode.BACKSPACE and self.cursor_pos > 0:
            # Delete character before cursor
            self.text = (self.text[:self.cursor_pos-1] + 
                        self.text[self.cursor_pos:])
            self.cursor_pos -= 1
        
        elif event.key_code == KeyCode.DELETE and self.cursor_pos < len(self.text):
            # Delete character at cursor
            self.text = (self.text[:self.cursor_pos] + 
                        self.text[self.cursor_pos+1:])
        
        elif event.key_code == KeyCode.LEFT and self.cursor_pos > 0:
            self.cursor_pos -= 1
        
        elif event.key_code == KeyCode.RIGHT and self.cursor_pos < len(self.text):
            self.cursor_pos += 1
        
        elif event.key_code == KeyCode.HOME:
            self.cursor_pos = 0
        
        elif event.key_code == KeyCode.END:
            self.cursor_pos = len(self.text)
    
    def draw(self, renderer, row, col):
        """Draw the text input."""
        # Draw text
        renderer.draw_text(row, col, self.text)
        
        # Draw cursor
        renderer.move_cursor(row, col + self.cursor_pos)
        renderer.set_cursor_visibility(True)

# Usage
text_input = TextInput()

while True:
    renderer.clear()
    renderer.draw_text(0, 0, "Enter text:")
    text_input.draw(renderer, 1, 0)
    renderer.refresh()
    
    event = renderer.get_input()
    if event.key_code == KeyCode.ENTER:
        print(f"Entered: {text_input.text}")
        break
    text_input.handle_input(event)
```

## Animation and Updates

### Smooth Animation

Animate at a consistent frame rate:

```python
import time
from ttk import KeyCode

def animation_loop(renderer):
    """Run a smooth animation loop."""
    frame = 0
    target_fps = 60
    frame_time = 1.0 / target_fps
    
    while True:
        start_time = time.time()
        
        # Update animation
        frame += 1
        x = int(20 + 10 * (frame % 60) / 60.0)
        
        # Draw frame
        renderer.clear()
        renderer.draw_text(10, x, "●")
        renderer.draw_text(0, 0, f"Frame: {frame}")
        renderer.refresh()
        
        # Check for input (non-blocking)
        event = renderer.get_input(timeout_ms=0)
        if event and event.key_code == KeyCode.ESCAPE:
            break
        
        # Maintain frame rate
        elapsed = time.time() - start_time
        sleep_time = max(0, frame_time - elapsed)
        time.sleep(sleep_time)
```

### Periodic Updates

Update display periodically:

```python
import time

def periodic_update_loop(renderer):
    """Update display every second."""
    last_update = time.time()
    update_interval = 1.0  # 1 second
    
    while True:
        current_time = time.time()
        
        # Check if it's time to update
        if current_time - last_update >= update_interval:
            renderer.clear()
            renderer.draw_text(0, 0, f"Time: {time.strftime('%H:%M:%S')}")
            renderer.refresh()
            last_update = current_time
        
        # Check for input with short timeout
        event = renderer.get_input(timeout_ms=100)
        if event and event.key_code == KeyCode.ESCAPE:
            break
```

## File Operations

### File Viewer

A simple file viewer with scrolling:

```python
from ttk import KeyCode

class FileViewer:
    def __init__(self, filename):
        self.filename = filename
        self.lines = []
        self.scroll_offset = 0
        self.load_file()
    
    def load_file(self):
        """Load file contents."""
        try:
            with open(self.filename, 'r') as f:
                self.lines = f.readlines()
        except Exception as e:
            self.lines = [f"Error loading file: {e}"]
    
    def draw(self, renderer):
        """Draw the file contents."""
        rows, cols = renderer.get_dimensions()
        
        renderer.clear()
        
        # Draw title
        title = f" {self.filename} ".center(cols)
        renderer.draw_text(0, 0, title, color_pair=1,
                          attributes=TextAttribute.BOLD)
        
        # Draw file contents
        visible_rows = rows - 2
        for i in range(visible_rows):
            line_num = self.scroll_offset + i
            if line_num < len(self.lines):
                line = self.lines[line_num].rstrip('\n')
                if len(line) > cols:
                    line = line[:cols]
                renderer.draw_text(i + 1, 0, line)
        
        # Draw status
        status = f" Line {self.scroll_offset + 1}/{len(self.lines)} "
        renderer.draw_text(rows - 1, 0, status.ljust(cols), color_pair=2)
        
        renderer.refresh()
    
    def handle_input(self, event, rows):
        """Handle scrolling."""
        visible_rows = rows - 2
        max_offset = max(0, len(self.lines) - visible_rows)
        
        if event.key_code == KeyCode.UP:
            self.scroll_offset = max(0, self.scroll_offset - 1)
        elif event.key_code == KeyCode.DOWN:
            self.scroll_offset = min(max_offset, self.scroll_offset + 1)
        elif event.key_code == KeyCode.PAGE_UP:
            self.scroll_offset = max(0, self.scroll_offset - visible_rows)
        elif event.key_code == KeyCode.PAGE_DOWN:
            self.scroll_offset = min(max_offset, self.scroll_offset + visible_rows)
        elif event.key_code == KeyCode.HOME:
            self.scroll_offset = 0
        elif event.key_code == KeyCode.END:
            self.scroll_offset = max_offset

# Usage
viewer = FileViewer("example.txt")
renderer.init_color_pair(1, (255, 255, 255), (0, 0, 128))
renderer.init_color_pair(2, (0, 0, 0), (200, 200, 200))

while True:
    rows, cols = renderer.get_dimensions()
    viewer.draw(renderer)
    event = renderer.get_input()
    if event.key_code == KeyCode.ESCAPE:
        break
    viewer.handle_input(event, rows)
```

## Advanced Patterns

### Split Pane Layout

Two-pane layout with adjustable split:

```python
class SplitPane:
    def __init__(self):
        self.split_ratio = 0.5  # 50/50 split
    
    def draw(self, renderer):
        """Draw split pane layout."""
        rows, cols = renderer.get_dimensions()
        split_col = int(cols * self.split_ratio)
        
        # Draw left pane
        renderer.draw_text(0, 0, "Left Pane".center(split_col))
        renderer.draw_vline(0, split_col, '│', rows)
        
        # Draw right pane
        right_width = cols - split_col - 1
        renderer.draw_text(0, split_col + 1, "Right Pane".center(right_width))
    
    def adjust_split(self, delta):
        """Adjust split ratio."""
        self.split_ratio = max(0.2, min(0.8, self.split_ratio + delta))

# Usage
split_pane = SplitPane()

while True:
    renderer.clear()
    split_pane.draw(renderer)
    renderer.refresh()
    
    event = renderer.get_input()
    if event.char == '+':
        split_pane.adjust_split(0.05)
    elif event.char == '-':
        split_pane.adjust_split(-0.05)
    elif event.key_code == KeyCode.ESCAPE:
        break
```

### Scrollable List

A scrollable list with selection:

```python
from ttk import KeyCode, TextAttribute

class ScrollableList:
    def __init__(self, items):
        self.items = items
        self.selected = 0
        self.scroll_offset = 0
    
    def draw(self, renderer, row, col, height, width):
        """Draw the scrollable list."""
        # Draw items
        for i in range(height):
            item_index = self.scroll_offset + i
            if item_index >= len(self.items):
                break
            
            item = self.items[item_index]
            if len(item) > width:
                item = item[:width]
            
            if item_index == self.selected:
                # Highlight selected item
                renderer.draw_text(row + i, col, item.ljust(width),
                                 attributes=TextAttribute.REVERSE)
            else:
                renderer.draw_text(row + i, col, item.ljust(width))
    
    def handle_input(self, event, visible_height):
        """Handle list navigation."""
        if event.key_code == KeyCode.UP and self.selected > 0:
            self.selected -= 1
            # Scroll up if needed
            if self.selected < self.scroll_offset:
                self.scroll_offset = self.selected
        
        elif event.key_code == KeyCode.DOWN and self.selected < len(self.items) - 1:
            self.selected += 1
            # Scroll down if needed
            if self.selected >= self.scroll_offset + visible_height:
                self.scroll_offset = self.selected - visible_height + 1
        
        elif event.key_code == KeyCode.PAGE_UP:
            self.selected = max(0, self.selected - visible_height)
            self.scroll_offset = max(0, self.scroll_offset - visible_height)
        
        elif event.key_code == KeyCode.PAGE_DOWN:
            self.selected = min(len(self.items) - 1, 
                              self.selected + visible_height)
            max_offset = max(0, len(self.items) - visible_height)
            self.scroll_offset = min(max_offset, 
                                    self.scroll_offset + visible_height)

# Usage
items = [f"Item {i}" for i in range(100)]
list_view = ScrollableList(items)

while True:
    renderer.clear()
    list_view.draw(renderer, 2, 5, 20, 40)
    renderer.refresh()
    
    event = renderer.get_input()
    if event.key_code == KeyCode.ENTER:
        print(f"Selected: {list_view.items[list_view.selected]}")
        break
    list_view.handle_input(event, 20)
```

### Window Resize Handling

Responsive layout that adapts to window size:

```python
from ttk import KeyCode

class ResponsiveApp:
    def __init__(self):
        self.rows = 0
        self.cols = 0
    
    def update_dimensions(self, renderer):
        """Update cached dimensions."""
        self.rows, self.cols = renderer.get_dimensions()
    
    def draw(self, renderer):
        """Draw responsive layout."""
        renderer.clear()
        
        # Title bar (always at top)
        title = "Responsive Application".center(self.cols)
        renderer.draw_text(0, 0, title, color_pair=1)
        
        # Content area (adapts to size)
        content_height = self.rows - 2
        content_width = self.cols - 4
        
        if content_height > 0 and content_width > 0:
            # Draw content box
            renderer.draw_rect(1, 2, content_height, content_width, filled=False)
            
            # Draw centered message
            message = f"Window: {self.rows}x{self.cols}"
            msg_row = 1 + content_height // 2
            msg_col = 2 + (content_width - len(message)) // 2
            renderer.draw_text(msg_row, msg_col, message)
        
        # Status bar (always at bottom)
        status = "Press ESC to quit".ljust(self.cols)
        renderer.draw_text(self.rows - 1, 0, status, color_pair=2)
        
        renderer.refresh()
    
    def run(self, renderer):
        """Main loop with resize handling."""
        renderer.init_color_pair(1, (255, 255, 255), (0, 0, 128))
        renderer.init_color_pair(2, (0, 0, 0), (200, 200, 200))
        
        self.update_dimensions(renderer)
        
        while True:
            self.draw(renderer)
            event = renderer.get_input()
            
            if event.key_code == KeyCode.RESIZE:
                # Window was resized
                self.update_dimensions(renderer)
            elif event.key_code == KeyCode.ESCAPE:
                break

# Usage
app = ResponsiveApp()
app.run(renderer)
```

## Summary

These examples demonstrate:
- Basic application structure
- Common UI components (menus, dialogs, progress bars)
- Input handling patterns
- Animation and periodic updates
- File operations
- Advanced layouts and responsive design

For more examples, see the demo applications in the `ttk/demo/` directory.
