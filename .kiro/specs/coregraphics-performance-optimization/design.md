# Design Document

## Overview

This document describes the design for optimizing the `drawRect_` method in the CoreGraphics backend of TFM. Profiling data has identified this method as a significant performance bottleneck. The current implementation iterates through every cell in the character grid (rows × cols) and makes individual CoreGraphics API calls for each cell, resulting in thousands of API calls per frame.

The optimization strategy focuses on:
1. **Batching** - Combining adjacent cells with the same background color into single draw calls
2. **Color caching** - Eliminating redundant NSColor object creation
3. **Coordinate optimization** - Reducing transformation overhead
4. **Culling** - Skipping cells outside the dirty region
5. **Native implementation evaluation** - Assessing whether Objective-C/Swift would provide additional gains

## Architecture

### Current Architecture (Inefficient)

```
drawRect_() called by Cocoa
    │
    ├─ For each row (0 to rows-1)
    │   └─ For each col (0 to cols-1)
    │       ├─ Calculate x, y coordinates
    │       ├─ Get color pair from grid
    │       ├─ Create NSColor for background (NEW OBJECT)
    │       ├─ Call setFill()
    │       ├─ Create NSRect (NEW OBJECT)
    │       ├─ Call NSRectFill() ← EXPENSIVE API CALL
    │       ├─ If char != ' ':
    │       │   ├─ Create NSColor for foreground (NEW OBJECT)
    │       │   ├─ Apply font attributes
    │       │   ├─ Create NSAttributedString (NEW OBJECT)
    │       │   └─ Call drawAtPoint_() ← EXPENSIVE API CALL
    │
    └─ Draw cursor if visible

For a 24×80 grid: 1,920 cells × 2 API calls = 3,840+ API calls per frame!
```

### Optimized Architecture

```
drawRect_() called by Cocoa
    │
    ├─ Initialize color cache (if not exists)
    ├─ Calculate dirty region from rect parameter
    │
    ├─ Phase 1: Batch Background Rectangles
    │   └─ For each row in dirty region
    │       └─ Scan row for consecutive cells with same bg color
    │           ├─ Accumulate into batch
    │           └─ When color changes or row ends:
    │               ├─ Get cached NSColor
    │               ├─ Call setFill() once
    │               └─ Call NSRectFill() once for entire batch
    │
    ├─ Phase 2: Draw Characters
    │   └─ For each row in dirty region
    │       └─ For each col with non-space char
    │           ├─ Get cached NSColor for foreground
    │           ├─ Get cached font (with attributes)
    │           ├─ Create NSAttributedString
    │           └─ Call drawAtPoint_()
    │
    └─ Draw cursor if visible

For a 24×80 grid with typical content:
- Background: ~50-100 batched calls (vs 1,920)
- Characters: ~500-800 calls (vs 1,920)
- Total: ~600-900 calls (vs 3,840+)
- Reduction: 75-85% fewer API calls
```

## Components and Interfaces

### 1. Color Cache

**Purpose**: Eliminate redundant NSColor object creation

**Interface**:
```python
class ColorCache:
    """Cache for NSColor objects to avoid repeated creation"""
    
    def __init__(self, max_size: int = 256):
        """Initialize color cache with maximum size"""
        self._cache: Dict[Tuple[int, int, int], Any] = {}  # RGB tuple -> NSColor
        self._max_size = max_size
    
    def get_color(self, r: int, g: int, b: int, alpha: float = 1.0) -> Any:
        """
        Get cached NSColor or create and cache if not exists
        
        Args:
            r, g, b: RGB values (0-255)
            alpha: Alpha value (0.0-1.0)
            
        Returns:
            NSColor object
        """
        key = (r, g, b, int(alpha * 100))
        if key not in self._cache:
            if len(self._cache) >= self._max_size:
                # Simple LRU: clear half the cache
                self._cache.clear()
            
            self._cache[key] = Cocoa.NSColor.colorWithRed_green_blue_alpha_(
                r / 255.0, g / 255.0, b / 255.0, alpha
            )
        return self._cache[key]
    
    def clear(self):
        """Clear the color cache"""
        self._cache.clear()
```

### 2. Rectangle Batcher

**Purpose**: Combine adjacent cells with same background color

**Interface**:
```python
class RectangleBatcher:
    """Batch consecutive rectangles with the same color"""
    
    def __init__(self):
        self._current_batch: Optional[RectBatch] = None
        self._batches: List[RectBatch] = []
    
    def add_cell(self, x: float, y: float, width: float, height: float,
                 bg_rgb: Tuple[int, int, int]):
        """
        Add a cell to the current batch or start a new batch
        
        Args:
            x, y: Cell position
            width, height: Cell dimensions
            bg_rgb: Background color RGB tuple
        """
        if self._current_batch is None:
            # Start new batch
            self._current_batch = RectBatch(x, y, width, height, bg_rgb)
        elif self._can_extend_batch(x, y, bg_rgb):
            # Extend current batch
            self._current_batch.extend(width)
        else:
            # Finish current batch and start new one
            self._batches.append(self._current_batch)
            self._current_batch = RectBatch(x, y, width, height, bg_rgb)
    
    def _can_extend_batch(self, x: float, y: float, 
                         bg_rgb: Tuple[int, int, int]) -> bool:
        """Check if cell can be added to current batch"""
        if self._current_batch is None:
            return False
        
        # Same row, same color, adjacent position
        return (self._current_batch.y == y and
                self._current_batch.bg_rgb == bg_rgb and
                abs(self._current_batch.right_edge() - x) < 0.1)
    
    def finish_row(self):
        """Finish current batch at end of row"""
        if self._current_batch is not None:
            self._batches.append(self._current_batch)
            self._current_batch = None
    
    def get_batches(self) -> List[RectBatch]:
        """Get all batches and reset"""
        if self._current_batch is not None:
            self._batches.append(self._current_batch)
            self._current_batch = None
        
        result = self._batches
        self._batches = []
        return result

@dataclass
class RectBatch:
    """A batch of adjacent rectangles with the same color"""
    x: float
    y: float
    width: float
    height: float
    bg_rgb: Tuple[int, int, int]
    
    def extend(self, additional_width: float):
        """Extend the batch width"""
        self.width += additional_width
    
    def right_edge(self) -> float:
        """Get the right edge x-coordinate"""
        return self.x + self.width
```

### 3. Font Cache

**Purpose**: Cache font objects with attributes applied

**Interface**:
```python
class FontCache:
    """Cache for NSFont objects with attributes"""
    
    def __init__(self, base_font: Any):
        """Initialize with base font"""
        self._base_font = base_font
        self._cache: Dict[int, Any] = {}  # attributes bitmask -> NSFont
    
    def get_font(self, attributes: int) -> Any:
        """
        Get cached font with attributes or create and cache
        
        Args:
            attributes: TextAttribute bitmask
            
        Returns:
            NSFont object with attributes applied
        """
        if attributes not in self._cache:
            font = self._base_font
            
            if attributes & TextAttribute.BOLD:
                font_manager = Cocoa.NSFontManager.sharedFontManager()
                font = font_manager.convertFont_toHaveTrait_(
                    font, Cocoa.NSBoldFontMask
                )
            
            self._cache[attributes] = font
        
        return self._cache[attributes]
    
    def clear(self):
        """Clear the font cache"""
        self._cache.clear()
```

### 4. Dirty Region Calculator

**Purpose**: Determine which cells need to be redrawn

**Interface**:
```python
class DirtyRegionCalculator:
    """Calculate which cells are in the dirty region"""
    
    @staticmethod
    def get_dirty_cells(rect: Any, rows: int, cols: int,
                       char_width: float, char_height: float) -> Tuple[int, int, int, int]:
        """
        Calculate which cells intersect with the dirty rect
        
        Args:
            rect: NSRect indicating dirty region
            rows, cols: Grid dimensions
            char_width, char_height: Cell dimensions
            
        Returns:
            Tuple of (start_row, end_row, start_col, end_col)
        """
        # Convert rect coordinates to cell coordinates
        # Remember: CoreGraphics uses bottom-left origin
        
        # Calculate column range
        start_col = max(0, int(rect.origin.x / char_width))
        end_col = min(cols, int((rect.origin.x + rect.size.width) / char_width) + 1)
        
        # Calculate row range (with coordinate flip)
        # Bottom of rect in CG coords
        bottom_y = rect.origin.y
        # Top of rect in CG coords
        top_y = rect.origin.y + rect.size.height
        
        # Convert to TTK row coordinates
        # TTK row 0 is at top, CG y is at bottom
        start_row = max(0, rows - int(top_y / char_height) - 1)
        end_row = min(rows, rows - int(bottom_y / char_height))
        
        return (start_row, end_row, start_col, end_col)
```

### 5. Optimized drawRect_ Implementation

**Modifications to CoreGraphicsBackend**:

```python
class CoreGraphicsBackend(RendererABC):
    def __init__(self, ...):
        # ... existing initialization ...
        
        # Add caches
        self._color_cache = ColorCache()
        self._font_cache = FontCache(self.font)
        
    def drawRect_(self, rect):
        """Optimized rendering with batching and caching"""
        graphics_context = Cocoa.NSGraphicsContext.currentContext()
        if graphics_context is None:
            return
        
        # Calculate dirty region
        start_row, end_row, start_col, end_col = (
            DirtyRegionCalculator.get_dirty_cells(
                rect, self.rows, self.cols,
                self.char_width, self.char_height
            )
        )
        
        # Phase 1: Batch and draw backgrounds
        batcher = RectangleBatcher()
        
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                char, color_pair, attributes = self.grid[row][col]
                
                # Calculate position
                x = col * self.char_width
                y = (self.rows - row - 1) * self.char_height
                
                # Get colors
                if color_pair in self.color_pairs:
                    fg_rgb, bg_rgb = self.color_pairs[color_pair]
                else:
                    fg_rgb, bg_rgb = self.color_pairs[0]
                
                # Handle reverse video
                if attributes & TextAttribute.REVERSE:
                    fg_rgb, bg_rgb = bg_rgb, fg_rgb
                
                # Add to batch
                batcher.add_cell(x, y, self.char_width, self.char_height, bg_rgb)
            
            # Finish row
            batcher.finish_row()
        
        # Draw all batched backgrounds
        for batch in batcher.get_batches():
            bg_color = self._color_cache.get_color(*batch.bg_rgb)
            bg_color.setFill()
            
            cell_rect = Cocoa.NSMakeRect(
                batch.x, batch.y, batch.width, batch.height
            )
            Cocoa.NSRectFill(cell_rect)
        
        # Phase 2: Draw characters
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                char, color_pair, attributes = self.grid[row][col]
                
                # Skip spaces
                if char == ' ':
                    continue
                
                # Calculate position
                x = col * self.char_width
                y = (self.rows - row - 1) * self.char_height
                
                # Get colors
                if color_pair in self.color_pairs:
                    fg_rgb, bg_rgb = self.color_pairs[color_pair]
                else:
                    fg_rgb, bg_rgb = self.color_pairs[0]
                
                # Handle reverse video
                if attributes & TextAttribute.REVERSE:
                    fg_rgb, bg_rgb = bg_rgb, fg_rgb
                
                # Get cached color and font
                fg_color = self._color_cache.get_color(*fg_rgb)
                font = self._font_cache.get_font(attributes)
                
                # Build attributes dictionary
                text_attributes = {
                    Cocoa.NSFontAttributeName: font,
                    Cocoa.NSForegroundColorAttributeName: fg_color
                }
                
                # Apply underline if needed
                if attributes & TextAttribute.UNDERLINE:
                    text_attributes[Cocoa.NSUnderlineStyleAttributeName] = (
                        Cocoa.NSUnderlineStyleSingle
                    )
                
                # Create and draw attributed string
                attr_string = Cocoa.NSAttributedString.alloc().initWithString_attributes_(
                    char, text_attributes
                )
                attr_string.drawAtPoint_(Cocoa.NSMakePoint(x, y))
        
        # Draw cursor (unchanged)
        if self.cursor_visible:
            cursor_x = self.cursor_col * self.char_width
            cursor_y = (self.rows - self.cursor_row - 1) * self.char_height
            
            cursor_color = self._color_cache.get_color(255, 255, 255, 0.8)
            cursor_color.setFill()
            
            cursor_rect = Cocoa.NSMakeRect(
                cursor_x, cursor_y, self.char_width, self.char_height
            )
            Cocoa.NSRectFill(cursor_rect)
```

## Data Models

### RectBatch
```python
@dataclass
class RectBatch:
    """A batch of adjacent rectangles with the same color"""
    x: float              # Left edge x-coordinate
    y: float              # Bottom edge y-coordinate (CoreGraphics coords)
    width: float          # Total width of batch
    height: float         # Height of batch (single cell height)
    bg_rgb: Tuple[int, int, int]  # Background color RGB
```

### CacheEntry
```python
@dataclass
class CacheEntry:
    """Entry in color or font cache"""
    key: Tuple           # Cache key (RGB tuple or attributes)
    value: Any           # Cached object (NSColor or NSFont)
    access_count: int    # For LRU tracking (future enhancement)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Property 1: Visual output equivalence
*For any* character grid state, the optimized rendering should produce visually identical output to the original implementation
**Validates: Requirements 7.2**

Property 2: Batch coverage completeness
*For any* row of cells, the union of all batched rectangles should cover the entire row width
**Validates: Requirements 2.2**

Property 3: Color cache correctness
*For any* RGB color tuple, requesting the same color multiple times should return equivalent NSColor objects
**Validates: Requirements 3.4**

Property 4: Dirty region containment
*For any* dirty rect, all cells drawn should be within or intersecting the dirty region
**Validates: Requirements 5.4**

Property 5: API call reduction
*For any* frame render, the number of NSRectFill calls should be less than the number of cells in the grid
**Validates: Requirements 2.3**

Property 6: Font attribute preservation
*For any* text attribute combination, the cached font should have the same visual properties as a freshly created font
**Validates: Requirements 7.4**

## Native Implementation Evaluation

### Analysis of Native Language Options

#### Current Python Implementation Bottlenecks

1. **PyObjC Bridge Overhead**
   - Each CoreGraphics API call crosses the Python-Objective-C bridge
   - Object creation (NSColor, NSRect, NSAttributedString) involves bridge overhead
   - Method calls require name translation and parameter marshalling

2. **Python Loop Overhead**
   - Nested loops (rows × cols) execute in Python interpreter
   - Grid access and color pair lookups are Python operations
   - Coordinate calculations happen in Python

#### Objective-C/Swift Implementation Potential

**Advantages**:
- **Direct API Access**: No bridge overhead for CoreGraphics calls
- **Compiled Performance**: Loops and calculations run at native speed
- **Memory Efficiency**: Direct memory management, no Python object overhead
- **Optimization**: Compiler optimizations (LLVM) for tight loops

**Estimated Performance Gains**:
- Bridge elimination: 20-30% improvement
- Loop optimization: 10-20% improvement
- Memory efficiency: 5-10% improvement
- **Total potential: 35-60% improvement over optimized Python**

**Disadvantages**:
- **Complexity**: Requires Objective-C/Swift code in Python project
- **Maintainability**: Two languages to maintain
- **Build System**: Requires compilation step
- **Debugging**: More complex debugging across language boundary
- **Portability**: Ties implementation more tightly to macOS

#### Implementation Strategy

**Phase 1: Python Optimizations (Current Spec)**
- Implement batching, caching, and culling in Python
- Measure performance improvement
- Target: 75-85% reduction in API calls

**Phase 2: Native Implementation (If Needed)**
- If Phase 1 doesn't achieve target FPS (60+ FPS)
- Implement critical path in Objective-C:
  - Grid iteration and batching logic
  - Color and font caching
  - CoreGraphics API calls
- Keep Python interface for integration
- Use ctypes or PyObjC to call native code

**Decision Criteria**:
- If Python optimizations achieve 60+ FPS: Stop at Phase 1
- If Python optimizations achieve 40-60 FPS: Consider Phase 2
- If Python optimizations achieve <40 FPS: Proceed with Phase 2

### Native Implementation Architecture (If Needed)

```
Python Layer (tfm_main.py)
    │
    ├─ Call native renderer
    │
    ▼
Native Bridge (PyObjC or ctypes)
    │
    ├─ Pass grid data
    ├─ Pass color pairs
    │
    ▼
Objective-C/Swift Implementation
    │
    ├─ CoreGraphicsOptimizedRenderer.m
    │   ├─ Batch background rectangles
    │   ├─ Cache colors and fonts
    │   ├─ Direct CoreGraphics calls
    │   └─ Return to Python
    │
    └─ Compiled as dynamic library (.dylib)
```

**Native Code Structure**:
```objective-c
// CoreGraphicsOptimizedRenderer.h
@interface CoreGraphicsOptimizedRenderer : NSObject

- (void)renderGrid:(char**)grid
          colorPairs:(CGFloat**)colorPairs
                rows:(int)rows
                cols:(int)cols
           charWidth:(CGFloat)charWidth
          charHeight:(CGFloat)charHeight
             context:(CGContextRef)context;

@end
```

## Error Handling

### Cache Overflow
- **Scenario**: Color or font cache grows too large
- **Handling**: 
  - Implement simple LRU eviction (clear half when full)
  - Log warning if cache clears frequently
  - Monitor cache hit rate

### Invalid Dirty Region
- **Scenario**: Dirty rect has invalid coordinates
- **Handling**:
  - Clamp to valid grid bounds
  - Fall back to full redraw if calculation fails
  - Log warning for debugging

### Batch Creation Failure
- **Scenario**: Batching logic produces invalid rectangles
- **Handling**:
  - Validate batch dimensions before drawing
  - Fall back to cell-by-cell rendering for invalid batches
  - Log error with batch details

### Graphics Context Unavailable
- **Scenario**: currentContext() returns None
- **Handling**:
  - Skip rendering (already handled in current code)
  - No error message (expected during window minimize)

## Testing Strategy

### Unit Tests

Unit tests will verify specific behaviors:

1. **ColorCache Tests**
   - Test cache hit/miss behavior
   - Test cache size limits
   - Test color equivalence

2. **RectangleBatcher Tests**
   - Test batch creation for adjacent cells
   - Test batch splitting on color change
   - Test row boundary handling

3. **FontCache Tests**
   - Test font caching with attributes
   - Test bold font application
   - Test cache correctness

4. **DirtyRegionCalculator Tests**
   - Test coordinate conversion
   - Test boundary clamping
   - Test full-screen dirty rect

### Property-Based Tests

Property-based tests will verify universal properties:

1. **Visual Output Equivalence Property**
   - Generate random grid states
   - Render with both original and optimized code
   - Compare pixel-by-pixel output
   - **Validates: Requirements 7.2**

2. **Batch Coverage Property**
   - Generate random rows of cells
   - Create batches
   - Verify complete coverage
   - **Validates: Requirements 2.2**

3. **Color Cache Correctness Property**
   - Generate random RGB values
   - Request same colors multiple times
   - Verify color equivalence
   - **Validates: Requirements 3.4**

4. **API Call Reduction Property**
   - Generate random grid states
   - Count API calls in optimized version
   - Verify count < grid size
   - **Validates: Requirements 2.3**

### Integration Tests

Integration tests will verify end-to-end functionality:

1. **Performance Measurement Test**
   - Run TFM with profiling enabled
   - Measure FPS before optimization
   - Apply optimizations
   - Measure FPS after optimization
   - Verify 20%+ improvement
   - **Validates: Requirements 6.1, 6.4**

2. **Visual Correctness Test**
   - Render complex UI with many colors
   - Compare screenshots before/after
   - Verify pixel-perfect match
   - **Validates: Requirements 7.1, 7.2**

3. **Edge Case Test**
   - Test with single-cell dirty regions
   - Test with full-screen dirty regions
   - Test with empty grid
   - Test with all-space grid
   - **Validates: Requirements 7.3**

## Implementation Notes

### Coordinate System Handling

The coordinate transformation remains critical:
- TTK: Top-left origin (row 0 at top)
- CoreGraphics: Bottom-left origin (y=0 at bottom)
- Formula: `y = (rows - row - 1) * char_height`

This must be preserved in all optimizations.

### Batching Strategy

Batching works best for:
- Horizontal runs of same-color cells (common in status bars, borders)
- Large background areas (common in file lists)

Batching is less effective for:
- Highly varied content (syntax-highlighted code)
- Single-character color changes

Expected batch sizes:
- Status bar: 80-cell batches
- File list: 10-30 cell batches
- Mixed content: 3-5 cell batches

### Cache Sizing

**Color Cache**:
- Typical TFM usage: 10-20 unique colors
- Cache size: 256 entries (generous headroom)
- Memory: ~8KB (256 × 32 bytes per NSColor)

**Font Cache**:
- Possible combinations: 4 (normal, bold, underline, bold+underline)
- Cache size: 8 entries (all combinations + extras)
- Memory: ~1KB

### Performance Targets

Based on profiling data:
- Current FPS: ~15-20 FPS (unacceptable)
- Target FPS: 60 FPS (smooth)
- Minimum acceptable: 30 FPS

Expected improvements:
- Batching: 50-60% reduction in draw calls
- Caching: 20-30% reduction in object creation
- Culling: 10-20% reduction in work (depends on dirty region)
- **Total: 75-85% performance improvement**

If Python optimizations achieve 45-50 FPS, that's acceptable. If still below 30 FPS, proceed with native implementation.

## Future Enhancements

1. **Adaptive Batching**: Adjust batching strategy based on content type
2. **Texture Caching**: Cache rendered character glyphs as textures
3. **Incremental Rendering**: Only redraw changed cells
4. **Background Thread Rendering**: Prepare next frame while displaying current
5. **Metal Backend**: Use Metal instead of CoreGraphics for GPU acceleration
6. **Smart Dirty Tracking**: Track which cells changed instead of using NSRect
7. **Font Atlas**: Pre-render all characters to texture atlas

