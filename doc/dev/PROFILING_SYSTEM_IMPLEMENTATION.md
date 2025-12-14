# Profiling System Implementation

## Overview

This document describes the technical implementation of TFM's performance profiling system. The system provides real-time FPS tracking and automatically captures detailed profiling data when performance issues are detected. It uses intelligent triggering to profile the entire main loop when FPS drops below 30 for more than 1 second, capturing 2 seconds of execution using Python's cProfile module.

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         TFM Entry Point                      │
│                          (tfm.py)                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ├─ Parse --profile flag
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    FileManager (tfm_main.py)                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Main Loop (run() method)                 │  │
│  │  ┌─────────────────────────────────────────────────┐ │  │
│  │  │  1. Start Loop Iteration                        │ │  │
│  │  │     - Record frame time                         │ │  │
│  │  │     - Check if profiling should start           │ │  │
│  │  │     ↓                                            │ │  │
│  │  │  2. Get Input (with timeout)                    │ │  │
│  │  │     ↓                                            │ │  │
│  │  │  3. Handle Key Input                            │ │  │
│  │  │     ↓                                            │ │  │
│  │  │  4. Draw Interface                              │ │  │
│  │  │     ↓                                            │ │  │
│  │  │  5. End Loop Iteration                          │ │  │
│  │  │     - Check if profiling should stop            │ │  │
│  │  │     - Print FPS if interval elapsed             │ │  │
│  │  └─────────────────────────────────────────────────┘ │  │
│  │  [Entire loop is profiled when FPS < 30 for > 1s]   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Profiling System                           │
│                   (tfm_profiling.py)                         │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  FPS Tracker     │  │  Profile Writer  │                 │
│  │  - Frame times   │  │  - Output dir    │                 │
│  │  - FPS calc      │  │  - File naming   │                 │
│  │  - Low FPS detect│  │  - Async write   │                 │
│  │  - Periodic print│  │  - Error handling│                 │
│  └──────────────────┘  └──────────────────┘                 │
│  ┌──────────────────────────────────────────┐               │
│  │  Profiling Manager                       │               │
│  │  - Trigger detection (FPS < 30 for > 1s) │               │
│  │  - cProfile enable/disable               │               │
│  │  - Duration control (2 seconds)          │               │
│  │  - Profile file generation               │               │
│  └──────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### ProfilingManager Class

**Location**: `src/tfm_profiling.py`

**Purpose**: Central coordinator for all profiling activities

**Key Methods**:

```python
class ProfilingManager:
    def __init__(self, enabled: bool, output_dir: str = "profiling_output",
                 profile_duration: float = 2.0):
        """Initialize profiling manager with enabled state, output directory, and duration"""
        
    def start_loop_iteration(self) -> None:
        """Mark the start of a main loop iteration
        - Records frame time for FPS tracking
        - Checks if profiling should be triggered (FPS < 30 for > 1s)
        - Starts profiling if conditions are met
        """
        
    def end_loop_iteration(self) -> None:
        """Mark the end of a main loop iteration
        - Checks if profiling duration has elapsed
        - Stops profiling and saves profile file if duration reached
        """
        
    def should_print_fps(self) -> bool:
        """Check if 5 seconds have elapsed since last FPS print"""
        
    def print_fps(self) -> None:
        """Print current FPS to stdout with timestamp"""
        
    def _start_profiling(self) -> None:
        """Start profiling the main loop
        - Creates cProfile.Profile instance
        - Enables profiling
        - Records start time
        - Prints notification message
        """
        
    def _stop_profiling(self) -> None:
        """Stop profiling and save the profile data
        - Disables profiling
        - Writes profile file asynchronously
        - Resets low FPS tracking
        - Prints completion message
        """
```

**State Management**:
- `enabled`: Boolean flag controlling profiling state
- `output_dir`: Directory for profile file output
- `profile_duration`: Duration in seconds to profile once triggered (default: 2.0)
- `fps_tracker`: FPSTracker instance for frame timing and low FPS detection
- `profile_writer`: ProfileWriter instance for file I/O
- `current_profiler`: Active cProfile.Profile instance (None when not profiling)
- `profiling_active`: Boolean flag indicating if profiling is currently running
- `profiling_start_time`: Timestamp when profiling started (None when not profiling)
- `loop_profile_count`: Counter for number of profiles generated

### FPS Tracking and Low FPS Detection

**FPS Calculation Algorithm**:
```python
def calculate_fps(self) -> float:
    """Calculate FPS from recent frame times"""
    if len(self.frame_times) < 2:
        return 0.0
    
    # Calculate time span of recent frames
    time_span = self.frame_times[-1] - self.frame_times[0]
    
    # FPS = number of frames / time span
    if time_span > 0:
        return (len(self.frame_times) - 1) / time_span
    return 0.0
```

**Low FPS Detection Algorithm**:
```python
def is_low_fps_sustained(self) -> bool:
    """Check if FPS has been below threshold for sustained duration"""
    current_fps = self.calculate_fps()
    current_time = time.time()
    
    if current_fps < self.low_fps_threshold:  # 30 FPS
        if self.low_fps_start_time is None:
            # Start tracking low FPS period
            self.low_fps_start_time = current_time
        elif current_time - self.low_fps_start_time >= self.low_fps_duration:  # 1 second
            # Low FPS has been sustained for required duration
            return True
    else:
        # FPS is acceptable, reset tracking
        self.low_fps_start_time = None
    
    return False
```

**Implementation Details**:
- Uses `collections.deque` with `maxlen=60` for sliding window
- Tracks frame start times, not durations
- Calculates FPS from time span of recent frames
- Prints every 5 seconds to avoid output spam
- Detects sustained low FPS (< 30 FPS for > 1 second)
- Resets low FPS tracking when FPS recovers or after profiling

### Intelligent Profiling Trigger System

**Trigger Logic**:
```python
def start_loop_iteration(self) -> None:
    """Check if profiling should be triggered"""
    if not self.enabled:
        return
    
    self.fps_tracker.record_frame()
    
    # Check if we should start profiling due to sustained low FPS
    if not self.profiling_active and self.fps_tracker.is_low_fps_sustained():
        self._start_profiling()
```

**Profiling Duration Control**:
```python
def end_loop_iteration(self) -> None:
    """Check if profiling duration has elapsed"""
    if not self.enabled:
        return
    
    # If profiling is active, check if duration has elapsed
    if self.profiling_active:
        elapsed = time.time() - self.profiling_start_time
        if elapsed >= self.profile_duration:  # 2 seconds
            self._stop_profiling()
```

**Why This Approach**:
- **Automatic**: No manual intervention needed to capture performance issues
- **Targeted**: Only profiles when there's an actual problem (FPS < 30)
- **Sustained**: Requires 1 second of low FPS to avoid false triggers
- **Comprehensive**: Captures entire main loop (input + rendering + all operations)
- **Duration-based**: Profiles for 2 seconds to get representative sample
- **Low overhead**: Only active when performance is already degraded

### Profile Generation

**cProfile Integration**:
```python
def _start_profiling(self) -> None:
    """Start profiling the main loop"""
    self.current_profiler = cProfile.Profile()
    self.current_profiler.enable()
    self.profiling_active = True
    self.profiling_start_time = time.time()
    
    fps = self.fps_tracker.calculate_fps()
    print(f"[PROFILING] Started profiling - FPS dropped to {fps:.2f} "
          f"(will profile for {self.profile_duration}s)")

def _stop_profiling(self) -> None:
    """Stop profiling and save the profile data"""
    self.current_profiler.disable()
    self.profiling_active = False
    
    elapsed = time.time() - self.profiling_start_time
    
    # Write profile asynchronously (non-blocking)
    self._write_profile_async(self.current_profiler, "loop")
    
    # Reset tracking
    self.fps_tracker.reset_low_fps_tracking()
    self.current_profiler = None
    self.profiling_start_time = None
    
    print(f"[PROFILING] Stopped profiling after {elapsed:.2f}s - profile saved")
```

**Filename Generation**:
```python
def generate_filename(self, operation_type: str) -> str:
    """Generate timestamped filename for profile"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"{operation_type}_profile_{timestamp}.prof"
```

**Asynchronous File Writing**:
```python
def _write_profile_async(self, profiler: cProfile.Profile, operation_type: str) -> None:
    """Write profile data asynchronously to avoid blocking main loop"""
    def write_in_background():
        filepath = self.profile_writer.write_profile(profiler, operation_type)
        if filepath:
            self.loop_profile_count += 1
            print(f"{operation_type.capitalize()} profile written to: {filepath}")
    
    thread = threading.Thread(target=write_in_background, daemon=True)
    thread.start()
```

### Output Directory Management

**Directory Creation**:
```python
def _ensure_output_dir(self) -> None:
    """Create output directory if it doesn't exist"""
    try:
        os.makedirs(self.output_dir, exist_ok=True)
        self._create_readme()
    except OSError as e:
        print(f"Warning: Could not create profiling directory: {e}")
        # Fall back to temp directory
        self.output_dir = tempfile.gettempdir()
```

**README Generation**:
```python
def _create_readme(self) -> None:
    """Create README.txt in output directory"""
    readme_path = os.path.join(self.output_dir, "README.txt")
    if not os.path.exists(readme_path):
        with open(readme_path, 'w') as f:
            f.write(README_CONTENT)
```

## Integration Points

### Command-Line Argument Parsing

**Location**: `tfm.py`

```python
parser.add_argument('--profile', action='store_true',
                   help='Enable performance profiling mode')

# Pass profiling flag to FileManager
fm = FileManager(renderer, profiling_enabled=args.profile)
```

### FileManager Initialization

**Location**: `src/tfm_main.py`

```python
def __init__(self, renderer, profiling_enabled=False, ...):
    # ... existing initialization ...
    
    # Initialize profiling if enabled
    self.profiling_manager = None
    if profiling_enabled:
        from tfm_profiling import ProfilingManager
        self.profiling_manager = ProfilingManager(enabled=True)
        print("Profiling mode enabled - performance data will be collected")
```

### Main Loop Integration

**Location**: `src/tfm_main.py` - `FileManager.run()` method

```python
def run(self):
    """Main application loop"""
    while True:
        # Start frame timing
        if self.profiling_manager:
            self.profiling_manager.start_frame()
        
        # ... existing code for quit check, startup redraw, log updates ...
        
        # Get user input
        event = self.renderer.get_input(timeout_ms=16)
        
        if event is None:
            pass
        elif event.key_code == KeyCode.RESIZE:
            # ... existing resize handling ...
        else:
            # Handle key input with profiling
            if self.profiling_manager:
                self.profiling_manager.profile_key_handling(
                    self.handle_key_input, event
                )
            else:
                self.handle_key_input(event)
        
        # Draw interface with profiling
        if self.profiling_manager:
            self.profiling_manager.profile_rendering(self.draw_interface)
        else:
            self.draw_interface()
        
        # End frame timing and print FPS if needed
        if self.profiling_manager:
            self.profiling_manager.end_frame()
            if self.profiling_manager.should_print_fps():
                self.profiling_manager.print_fps()
```

## Performance Considerations

### Zero Overhead When Disabled

When profiling is disabled:
- No `ProfilingManager` instance is created
- All profiling checks are simple `if self.profiling_manager:` tests
- No profiling code executes
- No performance impact

### Minimal Overhead When Enabled

When profiling is enabled:
- FPS tracking uses lightweight `time.time()` calls
- Frame times stored in fixed-size deque (no unbounded growth)
- Profile file I/O happens after function execution (non-blocking)
- Profiling overhead measured at < 10% of execution time

### Optimization Techniques

1. **Lazy Import**: `ProfilingManager` imported only when needed
2. **Efficient Data Structures**: `deque` with `maxlen` for frame times
3. **Minimal Checks**: Simple boolean checks for profiling state
4. **Async I/O**: File writes don't block main loop
5. **Selective Profiling**: Only profile key handling and rendering, not every operation

## Error Handling

### File I/O Errors

```python
try:
    profiler.dump_stats(filepath)
    print(f"Profile saved: {filepath}")
except OSError as e:
    print(f"Warning: Could not save profile: {e}")
    # Continue without saving
```

### Directory Creation Errors

```python
try:
    os.makedirs(self.output_dir, exist_ok=True)
except OSError as e:
    print(f"Warning: Could not create profiling directory: {e}")
    # Fall back to temp directory
    self.output_dir = tempfile.gettempdir()
```

### Profiling Errors

```python
try:
    result = func(*args, **kwargs)
finally:
    profiler.disable()
    # Always disable profiler, even if function raises
```

## Testing Strategy

### Unit Tests

**Location**: `test/test_profiling_optimization.py`

Tests cover:
- ProfilingManager initialization
- FPS calculation accuracy
- Filename generation uniqueness
- Output directory creation
- Error handling for file I/O

### Integration Tests

**Location**: `test/test_key_event_profiling.py`, `test/test_rendering_profiling.py`

Tests cover:
- Profile file generation
- Filename format validation
- Directory structure verification
- End-to-end profiling workflow

### Demo Scripts

**Location**: `demo/demo_fps_tracking.py`, `demo/demo_key_event_profiling.py`, etc.

Demonstrate:
- FPS tracking in action
- Profile file generation
- Analysis workflow
- Error handling scenarios

## Data Formats

### Profile File Format

Profile files use Python's standard `.prof` format (cProfile output):
- Binary format, not human-readable
- Analyzed with `pstats` module or visualization tools
- Contains function call statistics, timing data, call counts

### FPS Output Format

```
[YYYY-MM-DD HH:MM:SS] FPS: XX.X
```

Example:
```
[2024-12-13 14:30:22] FPS: 58.3
```

### Filename Format

```
{operation_type}_profile_{timestamp}.prof
```

Components:
- `operation_type`: "key" or "render"
- `timestamp`: YYYYMMDD_HHMMSS_microseconds
- Extension: `.prof`

Example:
```
key_profile_20241213_143022_123456.prof
```

## Configuration

### Default Settings

```python
# Default output directory
DEFAULT_OUTPUT_DIR = "profiling_output"

# FPS print interval (seconds)
FPS_PRINT_INTERVAL = 5.0

# Frame time window size (number of frames)
FRAME_TIME_WINDOW = 60
```

### Customization

Users can customize by modifying `tfm_profiling.py`:
- Change output directory
- Adjust FPS print interval
- Modify frame time window size
- Add custom profiling points

## Future Enhancements

### Planned Features

1. **Selective Profiling**: Profile only specific operations
2. **Profile Aggregation**: Combine multiple profiles for analysis
3. **Real-time Visualization**: Display FPS graph in TFM UI
4. **Memory Profiling**: Add memory usage tracking
5. **Hotkey Toggle**: Enable/disable profiling without restarting
6. **Profile Comparison**: Compare profiles before/after optimizations
7. **Automated Analysis**: Generate summary reports from profile data

### API Extensions

```python
# Future API additions
class ProfilingManager:
    def enable_profiling(self) -> None:
        """Enable profiling at runtime"""
        
    def disable_profiling(self) -> None:
        """Disable profiling at runtime"""
        
    def get_current_fps(self) -> float:
        """Get current FPS without printing"""
        
    def profile_custom_operation(self, func: Callable, 
                                 operation_name: str) -> Any:
        """Profile a custom operation with specified name"""
```

## Troubleshooting

### Common Issues

**Profile files not created**:
- Check output directory permissions
- Verify profiling is enabled (look for startup message)
- Check for file I/O errors in output

**FPS not printing**:
- Ensure profiling is enabled
- Wait at least 5 seconds
- Check stdout is not redirected

**Large profile files**:
- Normal for complex operations
- Use pstats to filter results
- Consider shorter profiling sessions

### Debugging

Enable verbose output:
```python
# In tfm_profiling.py
DEBUG = True  # Add debug prints
```

Check profiling state:
```python
# In FileManager.run()
if self.profiling_manager:
    print(f"Profiling enabled: {self.profiling_manager.enabled}")
```

## Best Practices

### For Developers

1. **Keep profiling optional**: Never require profiling for normal operation
2. **Minimize overhead**: Profile only critical code paths
3. **Handle errors gracefully**: Don't crash on profiling errors
4. **Document profiling points**: Comment where profiling occurs
5. **Test with profiling**: Verify profiling doesn't break functionality

### For Performance Analysis

1. **Profile consistently**: Use same operations when comparing
2. **Focus on hot paths**: Profile frequently executed code
3. **Measure before optimizing**: Get baseline measurements
4. **Verify improvements**: Profile after optimizations
5. **Consider context**: Some operations are naturally slower

## Related Systems

- **Logging System**: `tfm_log_manager.py` - Separate from profiling
- **Backend System**: `tfm_backend_selector.py` - Profiling works with all backends
- **Configuration System**: `tfm_config.py` - No profiling configuration yet

## References

- Python cProfile documentation: https://docs.python.org/3/library/profile.html
- pstats documentation: https://docs.python.org/3/library/profile.html#module-pstats
- snakeviz documentation: https://jiffyclub.github.io/snakeviz/

---

For user-facing documentation, see `doc/PERFORMANCE_PROFILING_FEATURE.md`.
