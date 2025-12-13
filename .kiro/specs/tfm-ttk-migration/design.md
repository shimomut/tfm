# TFM → TTK Migration Design

## Overview

This design document describes the architecture for migrating TFM from direct curses usage to the TTK rendering library. The migration follows a gradual, component-by-component approach to maintain stability while enabling desktop application mode.

## Architecture

### Current Architecture (Pre-Migration)

```
┌─────────────────────────────────────────┐
│         TFM Application Code            │
│  (FileManager, PaneManager, Dialogs)    │
└─────────────────┬───────────────────────┘
                  │
                  │ Direct imports and calls
                  │
┌─────────────────▼───────────────────────┐
│         Python curses Library           │
│    (stdscr, color_pair, addstr, etc.)   │
└─────────────────────────────────────────┘
```

### Target Architecture (Post-Migration)

```
┌─────────────────────────────────────────┐
│         TFM Application Code            │
│  (FileManager, PaneManager, Dialogs)    │
└─────────────────┬───────────────────────┘
                  │
                  │ Uses TTK Renderer API directly
                  │
┌─────────────────▼───────────────────────┐
│          TTK Renderer API               │
│   (draw_text, draw_rect, get_input)     │
└─────────────────┬───────────────────────┘
                  │
                  │ Backend implementation
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼────────┐  ┌───────▼────────────┐
│ CursesBackend  │  │ CoreGraphics       │
│  (Terminal)    │  │  Backend (macOS)   │
└────────────────┘  └────────────────────┘
```

**Key Design Decision:** TFM will use TTK's API directly without an adapter layer. Since TTK already provides a clean, well-designed API (`draw_text()`, `get_input()`, etc.), there's no need to create a curses-like wrapper. This results in cleaner code and eliminates unnecessary abstraction.

## Component Design

### 1. Direct TTK API Usage

TFM will use TTK's Renderer API directly without an adapter layer. This approach is cleaner and more maintainable.

**Key Changes:**
- Replace `stdscr.addstr()` with `renderer.draw_text()`
- Replace `stdscr.getch()` with `renderer.get_input()`
- Replace `stdscr.getmaxyx()` with `renderer.get_dimensions()`
- Replace curses color pairs with RGB tuples
- Replace curses key codes with TTK's InputEvent and KeyCode

**Example Migration:**

```python
# Before (curses):
stdscr.addstr(row, col, text, curses.color_pair(1) | curses.A_BOLD)
key = stdscr.getch()
if key == curses.KEY_UP:
    # handle up arrow

# After (TTK):
from ttk import TextAttribute, KeyCode

renderer.draw_text(row, col, text, color_pair=1, attributes=TextAttribute.BOLD)
event = renderer.get_input()
if event and event.key_code == KeyCode.UP:
    # handle up arrow
```

### 2. Backend Selection Mechanism

```python
# src/tfm_backend_selector.py

import sys
import platform

def select_backend(args):
    """
    Select appropriate TTK backend based on arguments and platform.
    
    Args:
        args: Parsed command-line arguments
    
    Returns:
        Tuple of (backend_name, backend_options)
    """
    # Check command-line arguments
    if hasattr(args, 'backend'):
        backend_name = args.backend
    elif hasattr(args, 'desktop') and args.desktop:
        backend_name = 'coregraphics'
    else:
        # Check configuration
        from tfm_config import get_config
        config = get_config()
        backend_name = getattr(config, 'PREFERRED_BACKEND', 'curses')
    
    # Validate backend availability
    if backend_name == 'coregraphics':
        if platform.system() != 'Darwin':
            print("Error: CoreGraphics backend is only available on macOS", 
                  file=sys.stderr)
            print("Falling back to curses backend", file=sys.stderr)
            backend_name = 'curses'
        else:
            try:
                import objc
            except ImportError:
                print("Error: PyObjC is required for CoreGraphics backend", 
                      file=sys.stderr)
                print("Install with: pip install pyobjc-framework-Cocoa", 
                      file=sys.stderr)
                print("Falling back to curses backend", file=sys.stderr)
                backend_name = 'curses'
    
    # Prepare backend options
    backend_options = {}
    
    if backend_name == 'coregraphics':
        backend_options = {
            'window_title': 'TFM - TUI File Manager',
            'font_name': 'Menlo',
            'font_size': 14,
        }
    
    return backend_name, backend_options
```

### 3. Color System Migration

```python
# src/tfm_colors.py (migrated version)

from ttk import TextAttribute

# Color pair constants (unchanged)
COLOR_PAIR_DEFAULT = 0
COLOR_PAIR_STATUS = 1
COLOR_PAIR_SELECTED = 2
# ... etc

def init_colors(renderer, color_scheme='dark'):
    """
    Initialize color pairs using TTK renderer.
    
    Args:
        renderer: TTK Renderer instance
        color_scheme: Color scheme name
    """
    # Get color definitions for scheme
    colors = get_color_scheme(color_scheme)
    
    # Initialize each color pair
    for pair_id, (fg_rgb, bg_rgb) in colors.items():
        if pair_id > 0:  # Skip pair 0 (default)
            renderer.init_color_pair(pair_id, fg_rgb, bg_rgb)

def get_color_scheme(scheme_name):
    """
    Get color definitions for a scheme.
    
    Returns:
        Dict mapping pair_id to (fg_rgb, bg_rgb) tuples
    """
    schemes = {
        'dark': {
            COLOR_PAIR_DEFAULT: ((255, 255, 255), (0, 0, 0)),
            COLOR_PAIR_STATUS: ((0, 0, 0), (0, 255, 255)),
            COLOR_PAIR_SELECTED: ((255, 255, 0), (0, 0, 128)),
            # ... etc
        },
        # ... other schemes
    }
    
    return schemes.get(scheme_name, schemes['dark'])

# Helper functions return color_pair and attributes separately
def get_status_color():
    """Get status bar color pair."""
    return COLOR_PAIR_STATUS

def get_status_attributes():
    """Get status bar text attributes."""
    return TextAttribute.NORMAL

def get_selected_color():
    """Get selected item color pair."""
    return COLOR_PAIR_SELECTED

def get_selected_attributes():
    """Get selected item text attributes."""
    return TextAttribute.BOLD
```

### 4. Main Entry Point Update

```python
# tfm.py (updated)

def main():
    """Main entry point with backend selection."""
    parser = create_parser()
    
    # Add backend selection arguments
    parser.add_argument(
        '--backend',
        type=str,
        choices=['curses', 'coregraphics'],
        help='Rendering backend to use (default: curses)'
    )
    
    parser.add_argument(
        '--desktop',
        action='store_true',
        help='Run as desktop application (shorthand for --backend coregraphics)'
    )
    
    args = parser.parse_args()
    
    # Select backend
    from tfm_backend_selector import select_backend
    backend_name, backend_options = select_backend(args)
    
    # Create TTK renderer directly
    if backend_name == 'curses':
        from ttk.backends.curses_backend import CursesBackend
        renderer = CursesBackend()
    elif backend_name == 'coregraphics':
        from ttk.backends.coregraphics_backend import CoreGraphicsBackend
        renderer = CoreGraphicsBackend(**backend_options)
    else:
        raise ValueError(f"Unknown backend: {backend_name}")
    
    try:
        renderer.initialize()
        
        # Import and run main application
        from tfm_main import main as tfm_main
        tfm_main(renderer, 
                remote_log_port=args.remote_log_port,
                left_dir=args.left,
                right_dir=args.right)
    finally:
        renderer.shutdown()
```

## Migration Strategy

### Phase 1: Foundation
1. Create `tfm_backend_selector.py`
2. Update `tfm.py` entry point to use TTK directly
3. Update `tfm_colors.py` to use RGB colors
4. Test that TFM initializes with TTK

### Phase 2: Core Components
1. Update `tfm_main.py` to accept renderer instead of stdscr
2. Replace all `stdscr.addstr()` with `renderer.draw_text()`
3. Replace all `stdscr.getch()` with `renderer.get_input()`
4. Update input handling to use InputEvent
5. Test main functionality

### Phase 3: UI Components
1. Update each dialog class to use TTK API
2. Update pane manager to use TTK API
3. Update text viewer to use TTK API
4. Update all other UI components
5. Test each component

### Phase 4: Cleanup
1. Remove all `import curses` statements
2. Replace curses constants with TTK equivalents
3. Update key binding system
4. Update tests
5. Update documentation

## Key Design Decisions

### 1. Direct API Usage (No Adapter)
- **Decision**: Use TTK's Renderer API directly without adapter layer
- **Rationale**: TTK already provides clean API; no need to emulate curses
- **Trade-off**: More changes to TFM code, but cleaner long-term architecture
- **Benefit**: Eliminates unnecessary abstraction layer (TFM → adapter → TTK → curses)

### 2. Backend Selection
- **Decision**: Support both command-line and configuration-based selection
- **Rationale**: Flexibility for users and developers
- **Trade-off**: More code, but better UX

### 3. Color System
- **Decision**: Migrate to RGB colors immediately
- **Rationale**: TTK uses RGB, better color accuracy
- **Trade-off**: Need to convert existing color definitions

### 4. Input Handling
- **Decision**: Use TTK's InputEvent directly, update key binding system
- **Rationale**: InputEvent is more powerful than curses key codes
- **Trade-off**: Need to update key binding logic, but better long-term

### 5. Gradual Migration
- **Decision**: Migrate component-by-component
- **Rationale**: Maintain stability, test each component
- **Trade-off**: Takes longer, but safer

## Testing Strategy

### Unit Tests
- Test adapter methods individually
- Test color conversion functions
- Test input translation

### Integration Tests
- Test TFM with CursesBackend
- Test TFM with CoreGraphicsBackend
- Verify equivalent behavior

### Regression Tests
- Run all existing TFM tests
- Verify no functionality lost
- Check performance benchmarks

## Performance Considerations

### Adapter Overhead
- Minimal: Simple method forwarding
- Caching for key translation
- No significant performance impact

### Backend Performance
- CursesBackend: Equivalent to direct curses
- CoreGraphicsBackend: GPU-accelerated, potentially faster
- Target: 60 FPS for desktop mode

## Error Handling

### Backend Initialization Failures
- Graceful fallback to CursesBackend
- Clear error messages
- Helpful installation instructions

### Runtime Errors
- Catch and log rendering errors
- Continue operation when possible
- Provide user-friendly error messages

## Documentation Updates

### User Documentation
- Add desktop mode usage instructions
- Document backend selection options
- Update installation guide

### Developer Documentation
- Document adapter architecture
- Explain migration process
- Provide backend implementation guide
