# SearchDialog Animation Feature

## Overview

The SearchDialog component now includes animated progress indicators that provide visual feedback during search operations. Users can choose from three different animation patterns and configure the animation speed through the configuration system.

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

### Configuration Options

Add these settings to your TFM configuration file (`~/.tfm/config.py`):

```python
class Config(DefaultConfig):
    # Search animation settings
    SEARCH_ANIMATION_PATTERN = 'spinner'  # 'spinner', 'dots', or 'progress'
    SEARCH_ANIMATION_SPEED = 0.2          # Animation frame update interval in seconds
```

#### Configuration Details

- **SEARCH_ANIMATION_PATTERN**: Choose the animation style
  - `'spinner'`: Rotating spinner (default)
  - `'dots'`: Dot-based animation
  - `'progress'`: Progress bar animation

- **SEARCH_ANIMATION_SPEED**: Control animation speed
  - Value in seconds between frame updates
  - Default: `0.2` seconds
  - Smaller values = faster animation
  - Larger values = slower animation
  - Recommended range: `0.1` to `0.5`

## Implementation Details

### Architecture

The animation system consists of two main components:

1. **SearchProgressAnimator**: Handles animation logic
   - Manages animation patterns and timing
   - Provides thread-safe frame updates
   - Generates formatted progress indicators

2. **SearchDialog Integration**: Incorporates animation into search UI
   - Displays animated indicators during search
   - Resets animation on new searches
   - Thread-safe integration with search operations

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

The animation runs automatically when searches are active. No user interaction is required beyond configuration.

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
   - Adjust `SEARCH_ANIMATION_SPEED` value
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

### SearchProgressAnimator Class

```python
class SearchProgressAnimator:
    def __init__(self, config)
    def get_current_frame() -> str
    def reset() -> None
    def get_progress_indicator(result_count: int, is_searching: bool) -> str
```

### Configuration Constants

```python
# Default values
SEARCH_ANIMATION_PATTERN = 'spinner'
SEARCH_ANIMATION_SPEED = 0.2
```

### Animation Patterns

```python
patterns = {
    'spinner': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
    'dots': ['⠁', '⠂', '⠄', '⡀', '⢀', '⠠', '⠐', '⠈'],
    'progress': ['▏', '▎', '▍', '▌', '▋', '▊', '▉', '█']
}
```