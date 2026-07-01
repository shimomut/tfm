# Performance Monitoring Implementation

## Overview

This document describes the implementation of performance monitoring for the TTK library. The performance monitoring system tracks frame rate (FPS) and rendering time to help identify performance bottlenecks and verify that rendering backends meet performance requirements.

## Implementation

### Module: `ttk/demo/performance.py`

The performance monitoring is implemented in the `PerformanceMonitor` class, which provides comprehensive tracking of rendering performance metrics.

### Key Components

#### PerformanceMonitor Class

The `PerformanceMonitor` class tracks:
- **Frame rate (FPS)**: Current and average frames per second
- **Rendering time**: Average, minimum, and maximum render time per frame
- **Frame time**: Total time per frame including input handling
- **Uptime**: Total monitoring duration
- **Frame count**: Total number of frames processed

#### Core Methods

**Frame Tracking:**
- `start_frame()`: Mark the start of a new frame
- `get_fps()`: Get current FPS based on recent frames
- `get_average_fps()`: Get average FPS over entire monitoring period
- `get_frame_time_ms()`: Get average frame time in milliseconds

**Render Tracking:**
- `start_render()`: Mark the start of rendering operations
- `end_render()`: Mark the end of rendering operations
- `get_render_time_ms()`: Get average render time in milliseconds
- `get_min_render_time_ms()`: Get minimum render time
- `get_max_render_time_ms()`: Get maximum render time

**Statistics:**
- `get_total_frames()`: Get total frame count
- `get_uptime()`: Get monitoring uptime in seconds
- `get_summary()`: Get all metrics in a dictionary
- `reset()`: Reset all statistics

### Integration with Test Interface

The performance monitoring is integrated into the test interface (`ttk/demo/test_interface.py`) to provide real-time performance feedback:

1. **Initialization**: Performance monitor is created when test interface is initialized
2. **Frame Timing**: `start_frame()` is called at the beginning of each frame
3. **Render Timing**: `start_render()` and `end_render()` wrap the drawing operations
4. **Display**: Performance metrics are displayed in a dedicated section of the UI

### Performance Metrics Display

The test interface displays the following metrics:

```
Performance Metrics:
  FPS: 60.0 (avg: 58.5)
  Render time: 2.50ms
    Min: 1.20ms  Max: 5.80ms
  Frame time: 16.67ms
  Frames: 1234  Uptime: 21.1s
```

**Metric Descriptions:**
- **FPS**: Current frames per second based on recent frame times
- **avg FPS**: Average FPS over entire monitoring period
- **Render time**: Average time spent in rendering operations
- **Min/Max**: Minimum and maximum render times observed
- **Frame time**: Average total time per frame (includes input handling)
- **Frames**: Total number of frames processed
- **Uptime**: Time since monitoring started

## Design Decisions

### History-Based Averaging

The monitor uses a rolling window (default 60 frames) for calculating current FPS and render times. This provides:
- **Smooth metrics**: Averages out temporary spikes
- **Responsive**: Recent performance is weighted more heavily
- **Memory efficient**: Fixed-size deque prevents unbounded growth

### Separate Frame and Render Timing

Frame timing and render timing are tracked separately because:
- **Frame time** includes input handling, event processing, and delays
- **Render time** measures only the drawing operations
- This separation helps identify whether performance issues are in rendering or other parts of the application

### Millisecond Precision

Render times are reported in milliseconds because:
- More intuitive for developers (60 FPS = 16.67ms per frame)
- Appropriate precision for typical rendering operations
- Easier to compare against target frame times

## Usage Example

```python
from ttk.demo.performance import PerformanceMonitor

# Create monitor
monitor = PerformanceMonitor(history_size=60)

# Main loop
while running:
    # Start frame timing
    monitor.start_frame()
    
    # Start render timing
    monitor.start_render()
    
    # Perform rendering operations
    renderer.clear()
    renderer.draw_text(0, 0, "Hello, World!")
    renderer.refresh()
    
    # End render timing
    monitor.end_render()
    
    # Get metrics
    fps = monitor.get_fps()
    render_time = monitor.get_render_time_ms()
    
    # Display metrics
    print(f"FPS: {fps:.1f}, Render: {render_time:.2f}ms")
```

## Testing

### Unit Tests

The implementation includes comprehensive unit tests (`ttk/test/test_performance.py`) covering:

1. **Initialization**: Verify correct initial state
2. **Frame counting**: Verify frames are counted correctly
3. **Render time tracking**: Verify render time measurement accuracy
4. **FPS calculation**: Verify FPS calculation with known frame rates
5. **History limits**: Verify history size is respected
6. **Reset functionality**: Verify reset clears all statistics
7. **Edge cases**: Zero history size, very fast frames, no data scenarios

### Test Coverage

The performance monitoring module achieves 97% code coverage with 18 passing tests.

## Performance Considerations

### Minimal Overhead

The performance monitor is designed to have minimal impact on the application:
- Uses `time.time()` which is very fast
- Simple arithmetic operations for calculations
- Fixed-size deques prevent memory growth
- No complex data structures or algorithms

### Optional Monitoring

Performance monitoring can be disabled by:
- Not creating a `PerformanceMonitor` instance
- Passing `enable_performance_monitoring=False` to `TestInterface`
- This allows running without any monitoring overhead

## Requirements Validation

This implementation satisfies **Requirement 6.6**:

> WHEN the demo application runs THEN the system SHALL include performance metrics showing frame rate and rendering time

**Validation:**
- ✅ Frame rate (FPS) is tracked and displayed
- ✅ Rendering time per frame is tracked and displayed
- ✅ Metrics are shown in the demo UI
- ✅ Both current and average values are provided
- ✅ Additional metrics (min/max render time, uptime) enhance debugging

## Future Enhancements

Potential improvements for future versions:

1. **Performance Profiling**: Add detailed breakdown of rendering operations
2. **Performance Alerts**: Warn when FPS drops below threshold
3. **Historical Graphs**: Display FPS/render time trends over time
4. **Export Metrics**: Save performance data to file for analysis
5. **Comparison Mode**: Compare performance between backends

## Related Documentation

- [Test Interface Implementation](TEST_INTERFACE_IMPLEMENTATION.md) - Integration with test UI
- [Demo Application Structure](DEMO_STRUCTURE.md) - Overall demo architecture
- Requirements Document - Requirement 6.6 (performance metrics)
