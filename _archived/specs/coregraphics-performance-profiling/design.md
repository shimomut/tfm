# Design Document

## Overview

This document describes the design for a performance profiling system to investigate and optimize the CoreGraphics backend in TFM. The system will provide real-time FPS measurements and detailed profiling data for key event handling and rendering operations, enabling developers to identify performance bottlenecks and measure optimization improvements.

The profiling system is designed to be non-intrusive, activated via a command-line flag, and to have minimal impact on normal application performance when disabled.

## Architecture

### High-Level Architecture

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
│  │  │  1. Get Input (with timeout)                    │ │  │
│  │  │     ↓                                            │ │  │
│  │  │  2. Handle Key Input ← [Profile if enabled]     │ │  │
│  │  │     ↓                                            │ │  │
│  │  │  3. Draw Interface ← [Profile if enabled]       │ │  │
│  │  │     ↓                                            │ │  │
│  │  │  4. Update FPS Counter ← [If profiling enabled] │ │  │
│  │  └─────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Profiling System                           │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  FPS Tracker     │  │  cProfile Wrapper│                 │
│  │  - Frame times   │  │  - Key profiling │                 │
│  │  - FPS calc      │  │  - Render profile│                 │
│  │  - Periodic print│  │  - File output   │                 │
│  └──────────────────┘  └──────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Profiling Output Directory                      │
│  - key_profile_TIMESTAMP.prof                                │
│  - render_profile_TIMESTAMP.prof                             │
│  - FPS output to stdout                                      │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

1. **Startup**: Parse `--profile` flag and initialize profiling system if enabled
2. **Main Loop**: 
   - Track frame start time
   - Get input (with timeout for FPS updates)
   - Profile key handling if event received
   - Profile rendering
   - Update FPS counter
   - Print FPS every 5 seconds
3. **Shutdown**: Write final profiling data and print file locations

## Components and Interfaces

### 1. Profiling Manager (`tfm_profiling.py`)

**Purpose**: Central coordinator for all profiling activities

**Interface**:
```python
class ProfilingManager:
    def __init__(self, enabled: bool, output_dir: str = "profiling_output"):
        """Initialize profiling manager"""
        
    def start_frame(self) -> None:
        """Mark the start of a new frame for FPS tracking"""
        
    def end_frame(self) -> None:
        """Mark the end of a frame and update FPS"""
        
    def should_print_fps(self) -> bool:
        """Check if 5 seconds have elapsed since last FPS print"""
        
    def print_fps(self) -> None:
        """Print current FPS to stdout with timestamp"""
        
    def profile_key_handling(self, func: Callable, *args, **kwargs) -> Any:
        """Profile a key handling function and save results"""
        
    def profile_rendering(self, func: Callable, *args, **kwargs) -> Any:
        """Profile a rendering function and save results"""
        
    def get_output_dir(self) -> str:
        """Get the profiling output directory path"""
```

**Responsibilities**:
- Manage profiling state (enabled/disabled)
- Track frame times for FPS calculation
- Coordinate cProfile usage for key handling and rendering
- Generate timestamped filenames
- Ensure output directory exists
- Print FPS at regular intervals

### 2. FPS Tracker

**Purpose**: Measure and report frames per second

**Data Structure**:
```python
class FPSTracker:
    frame_times: deque[float]  # Recent frame timestamps
    last_print_time: float     # Last time FPS was printed
    print_interval: float      # Interval between prints (5 seconds)
```

**Methods**:
- `record_frame()`: Record current frame timestamp
- `calculate_fps()`: Calculate FPS from recent frame times
- `should_print()`: Check if print interval has elapsed
- `format_output()`: Format FPS output with timestamp

### 3. Profile Writer

**Purpose**: Write cProfile data to files with proper naming

**Interface**:
```python
class ProfileWriter:
    def __init__(self, output_dir: str):
        """Initialize with output directory"""
        
    def write_profile(self, profile_data: cProfile.Profile, 
                     operation_type: str) -> str:
        """Write profile data to file, return filename"""
        
    def generate_filename(self, operation_type: str) -> str:
        """Generate timestamped filename"""
        
    def ensure_output_dir(self) -> None:
        """Create output directory if it doesn't exist"""
```

### 4. Command-Line Integration

**Modification to `tfm.py`**:
```python
parser.add_argument('--profile', action='store_true',
                   help='Enable performance profiling mode')

# Pass profiling flag to FileManager
fm = FileManager(renderer, profiling_enabled=args.profile)
```

### 5. FileManager Integration

**Modifications to `FileManager.__init__()`**:
```python
def __init__(self, renderer, profiling_enabled=False, ...):
    # ... existing initialization ...
    
    # Initialize profiling if enabled
    self.profiling_manager = ProfilingManager(profiling_enabled) if profiling_enabled else None
    
    if self.profiling_manager:
        print("Profiling mode enabled - performance data will be collected")
```

**Modifications to `FileManager.run()`**:
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
    
    # ... existing cleanup code ...
```

## Data Models

### Frame Timing Data
```python
@dataclass
class FrameTimingData:
    """Data for a single frame"""
    start_time: float      # Frame start timestamp
    end_time: float        # Frame end timestamp
    duration: float        # Frame duration in seconds
```

### Profiling Session
```python
@dataclass
class ProfilingSession:
    """Data for a profiling session"""
    enabled: bool                    # Whether profiling is active
    output_dir: str                  # Directory for output files
    fps_tracker: FPSTracker          # FPS tracking component
    profile_writer: ProfileWriter    # Profile file writer
    key_profile_count: int           # Number of key profiles written
    render_profile_count: int        # Number of render profiles written
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Property 1: Profiling flag enables profiling mode
*For any* TFM launch with the `--profile` flag, profiling mode should be active and a message should be displayed
**Validates: Requirements 1.1, 1.2**

Property 2: FPS output format consistency
*For any* FPS output, the printed string should contain both a timestamp and an FPS value
**Validates: Requirements 2.3**

Property 3: Profile filename uniqueness
*For any* two profiling operations, the generated filenames should be unique (contain different timestamps)
**Validates: Requirements 3.4, 4.4, 6.3**

Property 4: Profile filename descriptiveness
*For any* profile file, the filename should indicate the operation type (key handling or rendering)
**Validates: Requirements 6.2**

Property 5: Output directory creation
*For any* profiling session, if the output directory does not exist at start, it should exist after the first profile write
**Validates: Requirements 6.1**

## Error Handling

### File I/O Errors
- **Scenario**: Cannot create output directory or write profile files
- **Handling**: 
  - Log error message to stderr
  - Continue profiling in memory
  - Attempt to write to fallback location (temp directory)
  - Do not crash the application

### Profiling Overhead Errors
- **Scenario**: Profiling causes significant performance degradation
- **Handling**:
  - Implement sampling-based profiling for rendering (not every frame)
  - Limit profile file size
  - Provide option to disable profiling mid-session (future enhancement)

### Invalid Profiling State
- **Scenario**: Profiling functions called when profiling is disabled
- **Handling**:
  - Check profiling_manager is not None before all profiling calls
  - Gracefully skip profiling operations
  - No error messages (expected behavior)

## Testing Strategy

### Unit Tests

Unit tests will verify specific behaviors and edge cases:

1. **ProfilingManager Initialization**
   - Test enabled/disabled states
   - Test output directory creation
   - Test default configuration values

2. **FPS Calculation**
   - Test FPS calculation with known frame times
   - Test print interval timing
   - Test output format

3. **Profile File Generation**
   - Test filename generation with timestamps
   - Test operation type in filenames
   - Test file writing

4. **Command-Line Parsing**
   - Test `--profile` flag recognition
   - Test default behavior without flag

### Property-Based Tests

Property-based tests will verify universal properties across many inputs:

1. **Filename Uniqueness Property**
   - Generate multiple timestamps
   - Verify all generated filenames are unique
   - **Validates: Requirements 3.4, 4.4, 6.3**

2. **FPS Output Format Property**
   - Generate random FPS values
   - Verify output always contains timestamp and FPS
   - **Validates: Requirements 2.3**

3. **Profile Filename Format Property**
   - Generate profiles for different operation types
   - Verify filenames always indicate operation type
   - **Validates: Requirements 6.2**

### Integration Tests

Integration tests will verify end-to-end functionality:

1. **Profiling Mode Activation**
   - Launch TFM with `--profile` flag
   - Verify profiling message appears
   - Verify profile files are created
   - **Validates: Requirements 1.1, 1.2, 3.3, 4.3**

2. **FPS Measurement**
   - Run TFM in profiling mode for 10+ seconds
   - Verify FPS is printed at 5-second intervals
   - **Validates: Requirements 2.1, 2.2**

3. **Profile File Organization**
   - Run profiling session
   - Verify output directory exists
   - Verify files are in correct location
   - **Validates: Requirements 6.1, 6.5**

### Performance Tests

Performance tests will verify profiling overhead is acceptable:

1. **Disabled Profiling Overhead**
   - Measure execution time without profiling
   - Verify no profiling code executes
   - **Validates: Requirements 7.1**

2. **Enabled Profiling Overhead**
   - Measure execution time with profiling
   - Verify overhead is less than 10%
   - **Validates: Requirements 7.5**

## Implementation Notes

### FPS Calculation Method

FPS will be calculated using a sliding window of recent frame times:

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

### cProfile Integration

cProfile will be used to profile specific function calls:

```python
import cProfile
import pstats

def profile_function(self, func, *args, **kwargs):
    """Profile a function call"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    try:
        result = func(*args, **kwargs)
    finally:
        profiler.disable()
        
    return result, profiler
```

### Timestamp Format

Timestamps will use ISO 8601 format with microseconds for uniqueness:

```python
from datetime import datetime

def generate_timestamp() -> str:
    """Generate timestamp for filenames"""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")
```

### Output Directory Structure

```
profiling_output/
├── key_profile_20241213_143022_123456.prof
├── key_profile_20241213_143025_789012.prof
├── render_profile_20241213_143022_234567.prof
├── render_profile_20241213_143025_890123.prof
└── README.txt  (explains how to analyze .prof files)
```

### Analyzing Profile Files

Profile files can be analyzed using Python's pstats module:

```bash
python -m pstats profiling_output/key_profile_*.prof
# Then use commands like:
# sort cumulative
# stats 20
# callers function_name
```

Or visualized using tools like snakeviz:

```bash
pip install snakeviz
snakeviz profiling_output/key_profile_*.prof
```

## Future Enhancements

1. **Selective Profiling**: Profile only specific operations (e.g., only key handling)
2. **Profile Aggregation**: Combine multiple profile files for analysis
3. **Real-time Visualization**: Display FPS graph in TFM UI
4. **Memory Profiling**: Add memory usage tracking
5. **Hotkey Toggle**: Enable/disable profiling without restarting
6. **Profile Comparison**: Compare profiles before/after optimizations
7. **Automated Analysis**: Generate summary reports from profile data
