# Progress Animation System

## Overview

TFM now includes a generalized progress animation system that provides visual feedback for various long-running operations. The system is built around the `ProgressAnimator` class and can be used for search operations, file operations, network tasks, and any other operations that benefit from animated progress indicators.

## Features

### Animation Patterns

1. **Spinner** (`'spinner'`)
   - Classic spinning indicator using Braille patterns
   - Frames: `⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏`
   - Smooth circular motion effect
   - Best for general use

2. **Dots** (`'dots'`)
   - Minimalist dot-based animation
   - Frames: `⠁ ⠂ ⠄ ⡀ ⢀ ⠠ ⠐ ⠈`
   - Subtle and clean appearance
   - Good for low-distraction environments

3. **Progress** (`'progress'`)
   - Progress bar style animation
   - Frames: `▏ ▎ ▍ ▌ ▋ ▊ ▉ █`
   - Shows filling progress bar effect
   - Visual representation of activity

4. **Bounce** (`'bounce'`)
   - Simple bouncing dot animation
   - Frames: `⠁ ⠂ ⠄ ⠂`
   - Minimal and rhythmic
   - Good for subtle feedback

5. **Pulse** (`'pulse'`)
   - Pulsing circle animation
   - Frames: `● ◐ ◑ ◒ ◓ ◔ ◕ ○`
   - Breathing effect
   - Calming and smooth

6. **Wave** (`'wave'`)
   - Wave-like vertical bars
   - Frames: `▁ ▂ ▃ ▄ ▅ ▆ ▇ █ ▇ ▆ ▅ ▄ ▃ ▂`
   - Flowing motion
   - Dynamic and engaging

7. **Clock** (`'clock'`)
   - Clock face animation
   - Frames: `🕐 🕑 🕒 🕓 🕔 🕕 🕖 🕗 🕘 🕙 🕚 🕛`
   - Time-based metaphor
   - Clear progression indication

8. **Arrow** (`'arrow'`)
   - Rotating arrow animation
   - Frames: `← ↖ ↑ ↗ → ↘ ↓ ↙`
   - Directional movement
   - Clear motion indication

### Configuration Options

Add these settings to your TFM configuration file (`~/.tfm/config.py`):

```python
class Config(DefaultConfig):
    # Progress animation settings (used by all components)
    PROGRESS_ANIMATION_PATTERN = 'spinner'  # Default pattern for all animations
    PROGRESS_ANIMATION_SPEED = 0.2          # Default speed for all animations
```

#### Configuration Details

- **PROGRESS_ANIMATION_PATTERN**: Animation pattern for all components
  - Available patterns: `'spinner'`, `'dots'`, `'progress'`, `'bounce'`, `'pulse'`, `'wave'`, `'clock'`, `'arrow'`
  - Default: `'spinner'`

- **PROGRESS_ANIMATION_SPEED**: Animation speed for all components
  - Value in seconds between frame updates
  - Default: `0.2` seconds
  - Smaller values = faster animation
  - Larger values = slower animation
  - Recommended range: `0.1` to `0.5`

## Implementation Details

### Architecture

The animation system consists of several components:

1. **ProgressAnimator**: Core animation engine
   - Manages animation patterns and timing
   - Provides thread-safe frame updates
   - Generates formatted progress indicators
   - Supports dynamic pattern and speed changes

2. **ProgressAnimatorFactory**: Factory for common use cases
   - `create_search_animator()`: Optimized for search operations
   - `create_loading_animator()`: Optimized for loading operations
   - `create_processing_animator()`: Optimized for processing operations
   - `create_custom_animator()`: Custom pattern and speed

3. **Component Integration**: Used throughout TFM
   - SearchDialog: Animated search progress
   - Future: File operations, network tasks, etc.
   - Consistent animation experience across all operations

### Thread Safety

The animation system is fully thread-safe:
- Animation state is managed independently of search threads
- Frame updates don't interfere with search operations
- Safe concurrent access to animation and search results

### Performance

The animation system has minimal performance impact:
- Lightweight frame calculations
- Efficient timing-based updates
- No impact on search speed or accuracy

## Usage Examples

### Basic Usage

Animations run automatically in supported operations. For search operations, no user interaction is required beyond configuration.

### Programmatic Usage

```python
from tfm_progress_animator import ProgressAnimator, ProgressAnimatorFactory

# Use factory for common scenarios
search_animator = ProgressAnimatorFactory.create_search_animator(config)
loading_animator = ProgressAnimatorFactory.create_loading_animator(config)

# Create custom animators
file_copy_animator = ProgressAnimatorFactory.create_custom_animator(
    config, 'progress', 0.3
)

# Generate status text
status = animator.get_status_text("Processing", "42 items", True)
# Output: "Processing ⠋ (42 items)"

# Dynamic configuration
animator.set_pattern('wave')  # Change pattern at runtime
animator.set_speed(0.1)       # Change speed at runtime
```

### Visual Examples

**Spinner Animation:**
```
Searching ⠋ (15 found)
Searching ⠙ (28 found)
Searching ⠹ (42 found)
```

**Dots Animation:**
```
Searching ⠁ (15 found)
Searching ⠂ (28 found)
Searching ⠄ (42 found)
```

**Progress Animation:**
```
Searching [█░░░░░░░] (15 found)
Searching [██░░░░░░] (28 found)
Searching [███░░░░░] (42 found)
```

## Behavior

### Animation Lifecycle

1. **Search Start**: Animation resets to first frame
2. **During Search**: Frames cycle at configured speed
3. **Search Complete**: Animation stops, shows final results
4. **Search Cancel**: Animation stops immediately
5. **New Search**: Animation resets and starts over

### Integration Points

- **Filename Search**: Shows animation during file system traversal
- **Content Search**: Shows animation during file content scanning
- **Pattern Changes**: Resets animation for new search patterns
- **Empty Patterns**: Stops animation and clears results

## Testing

The animation system includes comprehensive tests:

- **Unit Tests**: `test/test_search_animation.py`
  - Animation pattern functionality
  - Frame cycling and timing
  - Configuration integration

- **Integration Tests**: `test/test_search_animation_integration.py`
  - Full TFM component integration
  - Thread safety verification
  - Performance impact assessment

- **Demo Scripts**: `demo/demo_search_animation.py`
  - Interactive demonstration of all patterns
  - Configuration examples
  - Performance comparisons

## Troubleshooting

### Common Issues

1. **Animation Not Visible**
   - Check terminal Unicode support
   - Verify configuration syntax
   - Ensure animation speed isn't too slow

2. **Animation Too Fast/Slow**
   - Adjust `PROGRESS_ANIMATION_SPEED` value
   - Recommended range: 0.1 to 0.5 seconds

3. **Character Display Issues**
   - Some terminals may not support all Unicode characters
   - Try different animation patterns
   - Spinner pattern has best compatibility

### Compatibility

- **Terminal Requirements**: Unicode support recommended
- **Performance**: Minimal CPU impact
- **Memory**: Negligible memory usage
- **Thread Safety**: Fully thread-safe implementation

## Future Enhancements

Potential future improvements:

1. **Custom Patterns**: User-defined animation sequences
2. **Color Animation**: Colored progress indicators
3. **Adaptive Speed**: Animation speed based on search progress
4. **More Patterns**: Additional animation styles
5. **Progress Percentage**: Actual progress calculation for progress bar

## API Reference

### ProgressAnimator Class

```python
class ProgressAnimator:
    def __init__(self, config, pattern_override=None, speed_override=None)
    def get_current_frame() -> str
    def reset() -> None
    def set_pattern(pattern: str) -> None
    def set_speed(speed: float) -> None
    def get_available_patterns() -> List[str]
    def get_pattern_preview(pattern=None) -> List[str]
    def get_progress_indicator(context_info=None, is_active=True, style='default') -> str
    def get_status_text(operation_name: str, context_info=None, is_active=True) -> str
```

### ProgressAnimatorFactory Class

```python
class ProgressAnimatorFactory:
    @staticmethod
    def create_search_animator(config) -> ProgressAnimator
    def create_loading_animator(config) -> ProgressAnimator
    def create_processing_animator(config) -> ProgressAnimator
    def create_custom_animator(config, pattern='spinner', speed=0.2) -> ProgressAnimator
```

### Configuration Constants

```python
# Default values
PROGRESS_ANIMATION_PATTERN = 'spinner'
PROGRESS_ANIMATION_SPEED = 0.2
```

### Animation Patterns

```python
patterns = {
    'spinner': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
    'dots': ['⠁', '⠂', '⠄', '⡀', '⢀', '⠠', '⠐', '⠈'],
    'progress': ['▏', '▎', '▍', '▌', '▋', '▊', '▉', '█'],
    'bounce': ['⠁', '⠂', '⠄', '⠂'],
    'pulse': ['●', '◐', '◑', '◒', '◓', '◔', '◕', '○'],
    'wave': ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█', '▇', '▆', '▅', '▄', '▃', '▂'],
    'clock': ['🕐', '🕑', '🕒', '🕓', '🕔', '🕕', '🕖', '🕗', '🕘', '🕙', '🕚', '🕛'],
    'arrow': ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙']
}
```