# Progress Animation System

## Overview

The Progress Animation System provides animated progress indicators for various operations in TFM. It creates visual feedback for long-running operations like file copying, searching, and directory scanning.

## Architecture

### Core Classes

**ProgressAnimator**
- Base class for progress animations
- Manages animation state and timing
- Provides frame generation
- Handles animation lifecycle

**ProgressAnimatorFactory**
- Factory for creating animator instances
- Manages animator types and configurations
- Provides default animators for common operations
- Supports custom animator registration

### Animation Types

The system supports several animation types:

1. **Spinner**: Rotating character animation
2. **Progress Bar**: Percentage-based bar
3. **Dots**: Animated dots (e.g., "Loading...")
4. **Pulse**: Pulsing indicator
5. **Custom**: User-defined animations

## Implementation Details

### ProgressAnimator Base Class

```python
class ProgressAnimator:
    def __init__(self, frames, interval=0.1):
        """Initialize animator with frames and interval."""
        self.frames = frames
        self.interval = interval
        self.current_frame = 0
        self.last_update = time.time()
        
    def get_frame(self):
        """Get current animation frame."""
        now = time.time()
        if now - self.last_update >= self.interval:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.last_update = now
        return self.frames[self.current_frame]
        
    def reset(self):
        """Reset animation to first frame."""
        self.current_frame = 0
        self.last_update = time.time()
```

### Built-in Animators

**Spinner Animator**:
```python
spinner_frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
spinner = ProgressAnimator(spinner_frames, interval=0.08)
```

**Progress Bar Animator**:
```python
def create_progress_bar(width, progress):
    """Create progress bar frame."""
    filled = int(width * progress)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}] {progress*100:.0f}%"
```

**Dots Animator**:
```python
dots_frames = ['   ', '.  ', '.. ', '...']
dots = ProgressAnimator(dots_frames, interval=0.3)
```

### ProgressAnimatorFactory

```python
class ProgressAnimatorFactory:
    _animators = {}
    
    @classmethod
    def register(cls, name, animator_class):
        """Register custom animator type."""
        cls._animators[name] = animator_class
        
    @classmethod
    def create(cls, operation_type):
        """Create animator for operation type."""
        if operation_type in cls._animators:
            return cls._animators[operation_type]()
        return cls.get_default_animator()
        
    @classmethod
    def get_default_animator(cls):
        """Get default spinner animator."""
        return ProgressAnimator(
            ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
            interval=0.08
        )
```

## Animation Lifecycle

### Initialization

1. **Create Animator**: Factory creates appropriate animator
2. **Configure**: Set frames and timing
3. **Start**: Begin animation

### Runtime

1. **Update**: Update animation frame based on time
2. **Render**: Render current frame to UI
3. **Repeat**: Continue until operation completes

### Cleanup

1. **Stop**: Stop animation
2. **Clear**: Clear animation from display
3. **Release**: Release resources

## Integration Points

### Progress Manager Integration

The animation system integrates with progress manager:

- **Operation Start**: Create animator when operation starts
- **Progress Update**: Update animation on progress
- **Operation Complete**: Stop animation when done
- **Cancellation**: Handle operation cancellation

### UI Integration

Integrates with TFM's UI system:

- **Status Bar**: Display in status bar
- **Progress Dialog**: Display in progress dialog
- **Details Pane**: Display in details pane
- **Inline**: Display inline with operation

### Configuration System

Respects configuration options:

- `progress.animation_enabled`: Enable/disable animations
- `progress.animation_speed`: Animation speed multiplier
- `progress.animation_style`: Default animation style

## Performance Considerations

### Frame Rate Control

- **Interval-Based**: Update based on time interval
- **Throttling**: Limit update frequency
- **Adaptive**: Adjust based on system load

### Resource Usage

- **Minimal Memory**: Use small frame arrays
- **Efficient Rendering**: Only redraw when changed
- **CPU Usage**: Minimal CPU overhead

## Customization

### Custom Animators

Users can create custom animators:

```python
# Define custom frames
custom_frames = ['◐', '◓', '◑', '◒']

# Create custom animator
custom_animator = ProgressAnimator(custom_frames, interval=0.1)

# Register with factory
ProgressAnimatorFactory.register('custom', lambda: custom_animator)
```

### Animation Styles

Different styles for different operations:

- **File Copy**: Progress bar with percentage
- **Search**: Spinner with "Searching..."
- **Scan**: Dots with "Scanning..."
- **Network**: Pulse with "Connecting..."

## Error Handling

The system handles various error conditions:

- **Invalid Frames**: Validate frame data
- **Timing Errors**: Handle time calculation errors
- **Render Errors**: Handle rendering failures
- **Thread Errors**: Handle threading issues

## Testing Considerations

Key areas for testing:

- **Frame Generation**: Verify correct frames
- **Timing**: Verify correct timing intervals
- **Lifecycle**: Test start/stop/reset
- **Integration**: Test with progress manager
- **Performance**: Test with many animations
- **Thread Safety**: Test concurrent animations

## Related Documentation

- Progress Animation Feature - User documentation
- [Progress Manager System](PROGRESS_MANAGER_SYSTEM.md) - Progress management
- [Copy Progress Feature](../COPY_PROGRESS_FEATURE.md) - File copy progress
- [Search Animation Feature](../SEARCH_ANIMATION_FEATURE.md) - Search animation

## Future Enhancements

Potential improvements:

- **More Styles**: Additional animation styles
- **Color Animation**: Animated colors
- **Smooth Transitions**: Smooth frame transitions
- **Adaptive Speed**: Adjust speed based on operation
- **Custom Rendering**: Custom rendering backends
- **3D Effects**: Pseudo-3D animations
