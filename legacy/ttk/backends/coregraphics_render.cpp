// cpp_renderer.cpp - C++ rendering backend for CoreGraphics
// Provides direct CoreGraphics/CoreText API access for improved performance

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <CoreGraphics/CoreGraphics.h>
#include <CoreText/CoreText.h>
#include <CoreFoundation/CoreFoundation.h>
#include <objc/runtime.h>
#include <objc/message.h>

#include <string>
#include <vector>
#include <unordered_map>
#include <optional>
#include <cstdint>
#include <cmath>
#include <chrono>
#include <locale>
#include <codecvt>
#include <iostream>

// Module version
#define CPP_RENDERER_VERSION "1.0.0"

//=============================================================================
// Data Structures
//=============================================================================

// Cell structure representing a single grid cell
struct Cell {
    std::u16string character;  // UTF-16 encoded character
    int color_pair;            // Color pair ID
    int attributes;            // Text attributes (BOLD, UNDERLINE, etc.)
    bool is_wide;              // True if character occupies 2 grid cells (zenkaku)
};

// Color pair structure with packed RGB values
struct ColorPair {
    uint32_t fg_rgb;  // Foreground RGB: 0x00RRGGBB
    uint32_t bg_rgb;  // Background RGB: 0x00RRGGBB
};

//=============================================================================
// ColorCache Class
//=============================================================================

/**
 * Cache for CGColorRef objects to avoid repeated color creation.
 * Implements LRU eviction when cache reaches maximum size.
 */
class ColorCache {
private:
    // Cache storage: packed RGB -> CGColorRef
    std::unordered_map<uint32_t, CGColorRef> cache_;
    
    // Maximum cache size before LRU eviction
    size_t max_size_;
    
    // LRU tracking: packed RGB -> access order
    std::unordered_map<uint32_t, size_t> access_order_;
    size_t access_counter_;
    
public:
    /**
     * Constructor.
     * @param max_size Maximum number of colors to cache (default 256)
     */
    explicit ColorCache(size_t max_size = 256)
        : max_size_(max_size), access_counter_(0) {
    }
    
    /**
     * Destructor - releases all cached CGColorRef objects.
     */
    ~ColorCache() {
        clear();
    }
    
    // Disable copy and move to prevent double-free
    ColorCache(const ColorCache&) = delete;
    ColorCache& operator=(const ColorCache&) = delete;
    ColorCache(ColorCache&&) = delete;
    ColorCache& operator=(ColorCache&&) = delete;
    
    /**
     * Get a CGColorRef for the specified RGB values.
     * Creates and caches the color if not already cached.
     * Implements LRU eviction when cache is full.
     * 
     * @param r Red component (0-255)
     * @param g Green component (0-255)
     * @param b Blue component (0-255)
     * @param alpha Alpha component (0.0-1.0, default 1.0)
     * @return CGColorRef for the specified color (caller does not own, do not release)
     */
    CGColorRef get_color(uint8_t r, uint8_t g, uint8_t b, float alpha = 1.0f) {
        // Pack RGB into uint32_t key (alpha not included in key for simplicity)
        uint32_t key = (static_cast<uint32_t>(r) << 16) |
                       (static_cast<uint32_t>(g) << 8) |
                       static_cast<uint32_t>(b);
        
        // Check if color is already cached
        auto it = cache_.find(key);
        if (it != cache_.end()) {
            // Update access order for LRU
            access_order_[key] = access_counter_++;
            return it->second;
        }
        
        // Create new CGColorRef
        CGFloat components[4] = {
            r / 255.0f,
            g / 255.0f,
            b / 255.0f,
            alpha
        };
        
        CGColorSpaceRef color_space = CGColorSpaceCreateDeviceRGB();
        if (color_space == nullptr) {
            throw std::runtime_error("Failed to create RGB color space");
        }
        
        CGColorRef color = CGColorCreate(color_space, components);
        CGColorSpaceRelease(color_space);
        
        if (color == nullptr) {
            throw std::runtime_error("Failed to create CGColor");
        }
        
        // Implement LRU eviction if cache is full
        if (cache_.size() >= max_size_) {
            // Find least recently used entry
            uint32_t lru_key = 0;
            size_t min_access = SIZE_MAX;
            
            for (const auto& entry : access_order_) {
                if (entry.second < min_access) {
                    min_access = entry.second;
                    lru_key = entry.first;
                }
            }
            
            // Remove LRU entry
            auto lru_it = cache_.find(lru_key);
            if (lru_it != cache_.end()) {
                CGColorRelease(lru_it->second);
                cache_.erase(lru_it);
                access_order_.erase(lru_key);
            }
        }
        
        // Add to cache
        cache_[key] = color;
        access_order_[key] = access_counter_++;
        
        return color;
    }
    
    /**
     * Clear all cached colors and release CGColorRef objects.
     */
    void clear() {
        // Release all CGColorRef objects
        for (auto& entry : cache_) {
            if (entry.second != nullptr) {
                CGColorRelease(entry.second);
            }
        }
        
        // Clear maps
        cache_.clear();
        access_order_.clear();
        access_counter_ = 0;
    }
    
    /**
     * Get current cache size.
     * @return Number of colors currently cached
     */
    size_t size() const {
        return cache_.size();
    }
    
    /**
     * Get maximum cache size.
     * @return Maximum number of colors that can be cached
     */
    size_t max_size() const {
        return max_size_;
    }
};

//=============================================================================
// FontCache Class
//=============================================================================

/**
 * Cache for CTFont objects to avoid repeated font creation.
 * Caches fonts with different attributes (BOLD, etc.).
 */
class FontCache {
private:
    // Base font reference (retained)
    CTFontRef base_font_;
    
    // Cache storage: attributes -> CTFontRef
    // Attributes are stored as integer bitmask
    std::unordered_map<int, CTFontRef> cache_;
    
public:
    /**
     * Constructor.
     * @param base_font Base CTFontRef to use for creating attributed fonts (retained)
     */
    explicit FontCache(CTFontRef base_font)
        : base_font_(base_font) {
        // Retain the base font
        if (base_font_ != nullptr) {
            CFRetain(base_font_);
        }
    }
    
    /**
     * Destructor - releases all cached CTFontRef objects and base font.
     */
    ~FontCache() {
        clear();
        
        // Release base font
        if (base_font_ != nullptr) {
            CFRelease(base_font_);
            base_font_ = nullptr;
        }
    }
    
    // Disable copy and move to prevent double-free
    FontCache(const FontCache&) = delete;
    FontCache& operator=(const FontCache&) = delete;
    FontCache(FontCache&&) = delete;
    FontCache& operator=(FontCache&&) = delete;
    
    /**
     * Get a CTFontRef for the specified attributes.
     * Creates and caches the font if not already cached.
     * 
     * @param attributes Attribute bitmask (e.g., BOLD = 1, UNDERLINE = 2)
     * @return CTFontRef for the specified attributes (caller does not own, do not release)
     */
    CTFontRef get_font(int attributes) {
        // Check if font with these attributes is already cached
        auto it = cache_.find(attributes);
        if (it != cache_.end()) {
            return it->second;
        }
        
        // Start with base font
        CTFontRef font = base_font_;
        
        // Apply BOLD attribute if needed (attribute bit 0)
        if (attributes & 1) {
            // Create bold variant using symbolic traits
            CTFontRef bold_font = CTFontCreateCopyWithSymbolicTraits(
                base_font_,
                0.0,  // Use same size as base font
                nullptr,  // No transform
                kCTFontBoldTrait,  // Add bold trait
                kCTFontBoldTrait   // Mask: only modify bold trait
            );
            
            if (bold_font != nullptr) {
                font = bold_font;
            } else {
                // If bold variant creation fails, use base font
                // Retain base font since we're caching it
                font = base_font_;
                CFRetain(font);
            }
        } else {
            // No BOLD attribute, use base font
            CFRetain(base_font_);
        }
        
        // Cache the font
        cache_[attributes] = font;
        
        return font;
    }
    
    /**
     * Clear all cached fonts and release CTFontRef objects.
     * Does not release the base font.
     */
    void clear() {
        // Release all cached CTFontRef objects
        for (auto& entry : cache_) {
            if (entry.second != nullptr) {
                CFRelease(entry.second);
            }
        }
        
        // Clear cache map
        cache_.clear();
    }
    
    /**
     * Get current cache size.
     * @return Number of fonts currently cached
     */
    size_t size() const {
        return cache_.size();
    }
    
    /**
     * Get base font reference.
     * @return Base CTFontRef (caller does not own, do not release)
     */
    CTFontRef base_font() const {
        return base_font_;
    }
};

//=============================================================================
// AttributeDictCache Class
//=============================================================================

/**
 * Cache for CFDictionary objects containing text attributes.
 * Combines font and color information into attribute dictionaries
 * used by CoreText for rendering.
 */
class AttributeDictCache {
private:
    // References to font and color caches (not owned)
    FontCache* font_cache_;
    ColorCache* color_cache_;
    
    // Cache storage: composite key -> CFDictionaryRef
    // Key is composed of: (font_attributes << 32) | (color_rgb) | (underline << 31)
    std::unordered_map<uint64_t, CFDictionaryRef> cache_;
    
    // Performance metrics
    size_t hits_;
    size_t misses_;
    
    /**
     * Create a composite cache key from font attributes, color, and underline flag.
     * 
     * @param font_attributes Font attribute bitmask
     * @param color_rgb Packed RGB color value
     * @param underline Whether underline is enabled
     * @return 64-bit composite key
     */
    uint64_t make_key(int font_attributes, uint32_t color_rgb, bool underline) const {
        // Pack into 64-bit key:
        // - Bits 0-31: color_rgb
        // - Bits 32-62: font_attributes (31 bits)
        // - Bit 63: underline flag
        uint64_t key = static_cast<uint64_t>(color_rgb);
        key |= (static_cast<uint64_t>(font_attributes & 0x7FFFFFFF) << 32);
        if (underline) {
            key |= (1ULL << 63);
        }
        return key;
    }
    
public:
    /**
     * Constructor.
     * 
     * @param font_cache Pointer to FontCache (not owned, must outlive this object)
     * @param color_cache Pointer to ColorCache (not owned, must outlive this object)
     */
    AttributeDictCache(FontCache* font_cache, ColorCache* color_cache)
        : font_cache_(font_cache)
        , color_cache_(color_cache)
        , hits_(0)
        , misses_(0) {
        
        if (font_cache_ == nullptr) {
            throw std::invalid_argument("FontCache pointer cannot be null");
        }
        if (color_cache_ == nullptr) {
            throw std::invalid_argument("ColorCache pointer cannot be null");
        }
    }
    
    /**
     * Destructor - releases all cached CFDictionaryRef objects.
     */
    ~AttributeDictCache() {
        clear();
    }
    
    // Disable copy and move to prevent double-free
    AttributeDictCache(const AttributeDictCache&) = delete;
    AttributeDictCache& operator=(const AttributeDictCache&) = delete;
    AttributeDictCache(AttributeDictCache&&) = delete;
    AttributeDictCache& operator=(AttributeDictCache&&) = delete;
    
    /**
     * Get a CFDictionaryRef containing text attributes.
     * Creates and caches the dictionary if not already cached.
     * 
     * @param font_attributes Font attribute bitmask (e.g., BOLD = 1)
     * @param color_rgb Packed RGB color value (0x00RRGGBB)
     * @param underline Whether to apply underline style
     * @return CFDictionaryRef for the specified attributes (caller does not own, do not release)
     */
    CFDictionaryRef get_attributes(int font_attributes, uint32_t color_rgb, bool underline) {
        // Create cache key
        uint64_t key = make_key(font_attributes, color_rgb, underline);
        
        // Check if attributes are already cached
        auto it = cache_.find(key);
        if (it != cache_.end()) {
            hits_++;
            return it->second;
        }
        
        // Cache miss - create new attribute dictionary
        misses_++;
        
        // Get font from FontCache
        CTFontRef font = font_cache_->get_font(font_attributes);
        if (font == nullptr) {
            throw std::runtime_error("Failed to get font from FontCache");
        }
        
        // Get color from ColorCache
        // Extract RGB components from packed value
        uint8_t r = (color_rgb >> 16) & 0xFF;
        uint8_t g = (color_rgb >> 8) & 0xFF;
        uint8_t b = color_rgb & 0xFF;
        
        CGColorRef color = color_cache_->get_color(r, g, b);
        if (color == nullptr) {
            throw std::runtime_error("Failed to get color from ColorCache");
        }
        
        // Build attribute dictionary
        // Start with font and foreground color (always present)
        CFStringRef keys[3];
        CFTypeRef values[3];
        CFIndex count = 2;
        
        keys[0] = kCTFontAttributeName;
        values[0] = font;
        
        keys[1] = kCTForegroundColorAttributeName;
        values[1] = color;
        
        // Add underline attribute if requested
        if (underline) {
            keys[2] = kCTUnderlineStyleAttributeName;
            // Create CFNumber for underline style (single underline)
            int underline_style = kCTUnderlineStyleSingle;
            CFNumberRef underline_number = CFNumberCreate(
                kCFAllocatorDefault,
                kCFNumberIntType,
                &underline_style
            );
            
            if (underline_number == nullptr) {
                throw std::runtime_error("Failed to create underline style number");
            }
            
            values[2] = underline_number;
            count = 3;
        }
        
        // Create CFDictionary
        CFDictionaryRef attr_dict = CFDictionaryCreate(
            kCFAllocatorDefault,
            (const void**)keys,
            (const void**)values,
            count,
            &kCFTypeDictionaryKeyCallBacks,
            &kCFTypeDictionaryValueCallBacks
        );
        
        // Release underline number if created
        if (underline && values[2] != nullptr) {
            CFRelease(values[2]);
        }
        
        if (attr_dict == nullptr) {
            throw std::runtime_error("Failed to create attribute dictionary");
        }
        
        // Cache the dictionary
        cache_[key] = attr_dict;
        
        return attr_dict;
    }
    
    /**
     * Clear all cached attribute dictionaries and release CFDictionaryRef objects.
     */
    void clear() {
        // Release all CFDictionaryRef objects
        for (auto& entry : cache_) {
            if (entry.second != nullptr) {
                CFRelease(entry.second);
            }
        }
        
        // Clear cache map
        cache_.clear();
    }
    
    /**
     * Get cache hit count.
     * @return Number of cache hits since last reset
     */
    size_t get_hit_count() const {
        return hits_;
    }
    
    /**
     * Get cache miss count.
     * @return Number of cache misses since last reset
     */
    size_t get_miss_count() const {
        return misses_;
    }
    
    /**
     * Reset performance metrics counters.
     */
    void reset_metrics() {
        hits_ = 0;
        misses_ = 0;
    }
    
    /**
     * Get current cache size.
     * @return Number of attribute dictionaries currently cached
     */
    size_t size() const {
        return cache_.size();
    }
};

//=============================================================================
// RectangleBatcher Class
//=============================================================================

/**
 * Batches adjacent cells with the same background color into rectangles
 * for efficient rendering with CGContextFillRect.
 * 
 * This class accumulates cells row-by-row and combines adjacent cells
 * with the same background color into single batches to minimize
 * the number of CoreGraphics API calls.
 */
class RectangleBatcher {
private:
    /**
     * Structure representing a batch of adjacent cells with the same background color.
     */
    struct RectBatch {
        CGFloat x;        // X coordinate (left edge)
        CGFloat y;        // Y coordinate (bottom edge in CoreGraphics coordinates)
        CGFloat width;    // Width of the batch
        CGFloat height;   // Height of the batch
        uint32_t bg_rgb;  // Background color (packed RGB: 0x00RRGGBB)
    };
    
    // Vector of completed batches
    std::vector<RectBatch> batches_;
    
    // Current batch being accumulated (optional, may be empty)
    std::optional<RectBatch> current_batch_;
    
public:
    /**
     * Constructor.
     * Initializes empty batches vector and no current batch.
     */
    RectangleBatcher()
        : batches_()
        , current_batch_(std::nullopt) {
    }
    
    /**
     * Destructor.
     */
    ~RectangleBatcher() = default;
    
    // Allow copy and move
    RectangleBatcher(const RectangleBatcher&) = default;
    RectangleBatcher& operator=(const RectangleBatcher&) = default;
    RectangleBatcher(RectangleBatcher&&) = default;
    RectangleBatcher& operator=(RectangleBatcher&&) = default;
    
    /**
     * Add a cell to the batcher.
     * If the cell can extend the current batch (same row, same color, adjacent),
     * it extends the batch. Otherwise, it finishes the current batch and starts a new one.
     * 
     * @param x X coordinate of the cell (left edge)
     * @param y Y coordinate of the cell (bottom edge in CoreGraphics coordinates)
     * @param width Width of the cell
     * @param height Height of the cell
     * @param bg_rgb Background color (packed RGB: 0x00RRGGBB)
     */
    void add_cell(CGFloat x, CGFloat y, CGFloat width, CGFloat height, uint32_t bg_rgb) {
        // Check if we can extend the current batch
        if (current_batch_.has_value()) {
            RectBatch& batch = current_batch_.value();
            
            // Can extend if:
            // 1. Same row (y coordinate matches)
            // 2. Same color
            // 3. Adjacent (x coordinate is at the right edge of current batch)
            bool same_row = (std::abs(batch.y - y) < 0.01f);  // Float comparison with epsilon
            bool same_color = (batch.bg_rgb == bg_rgb);
            bool adjacent = (std::abs((batch.x + batch.width) - x) < 0.01f);  // Float comparison
            
            if (same_row && same_color && adjacent) {
                // Extend current batch width
                batch.width += width;
                return;
            }
            
            // Cannot extend - finish current batch
            batches_.push_back(batch);
            current_batch_ = std::nullopt;
        }
        
        // Start new batch
        RectBatch new_batch;
        new_batch.x = x;
        new_batch.y = y;
        new_batch.width = width;
        new_batch.height = height;
        new_batch.bg_rgb = bg_rgb;
        
        current_batch_ = new_batch;
    }
    
    /**
     * Finish the current row.
     * Adds the current batch (if any) to the batches vector.
     * Call this at the end of each row to ensure batches don't span rows.
     */
    void finish_row() {
        if (current_batch_.has_value()) {
            batches_.push_back(current_batch_.value());
            current_batch_ = std::nullopt;
        }
    }
    
    /**
     * Get all batches and clear the batcher state.
     * 
     * @return Vector of completed batches
     */
    const std::vector<RectBatch>& get_batches() {
        // Finish any remaining batch
        if (current_batch_.has_value()) {
            batches_.push_back(current_batch_.value());
            current_batch_ = std::nullopt;
        }
        
        return batches_;
    }
    
    /**
     * Clear all batches and reset state.
     */
    void clear() {
        batches_.clear();
        current_batch_ = std::nullopt;
    }
    
    /**
     * Get the number of completed batches.
     * @return Number of batches
     */
    size_t size() const {
        return batches_.size();
    }
};

//=============================================================================
// Coordinate Transformation Utilities
//=============================================================================

/**
 * Structure representing a rectangular region of cells in the grid.
 */
struct CellRect {
    int start_row;    // Starting row (inclusive)
    int end_row;      // Ending row (exclusive)
    int start_col;    // Starting column (inclusive)
    int end_col;      // Ending column (exclusive)
};

/**
 * Convert TTK row coordinate to CoreGraphics y-coordinate.
 * TTK uses top-left origin (row 0 is at top), while CoreGraphics uses
 * bottom-left origin (y=0 is at bottom).
 * 
 * @param row TTK row coordinate (0 = top)
 * @param rows Total number of rows in grid
 * @param char_height Height of each character cell in pixels
 * @return CoreGraphics y-coordinate (bottom edge of the cell)
 */
static inline CGFloat ttk_to_cg_y(int row, int rows, CGFloat char_height) {
    // Formula: y = (rows - row - 1) * char_height
    // This converts from top-left origin to bottom-left origin
    return static_cast<CGFloat>(rows - row - 1) * char_height;
}

/**
 * Calculate which cells in the grid need to be redrawn based on a dirty rectangle.
 * Converts from CoreGraphics pixel coordinates to TTK cell coordinates.
 * 
 * @param dirty_rect CGRect in CoreGraphics coordinates (bottom-left origin)
 * @param char_width Width of each character cell in pixels
 * @param char_height Height of each character cell in pixels
 * @param rows Total number of rows in grid
 * @param cols Total number of columns in grid
 * @param offset_x X offset for centering the grid in the view
 * @param offset_y Y offset for centering the grid in the view
 * @return CellRect structure with cell coordinates to redraw
 */
static CellRect calculate_dirty_cells(
    CGRect dirty_rect,
    CGFloat char_width,
    CGFloat char_height,
    int rows,
    int cols,
    CGFloat offset_x,
    CGFloat offset_y
) {
    // Adjust dirty rect by offsets to get grid-relative coordinates
    CGFloat grid_x = dirty_rect.origin.x - offset_x;
    CGFloat grid_y = dirty_rect.origin.y - offset_y;
    CGFloat grid_right = grid_x + dirty_rect.size.width;
    CGFloat grid_top = grid_y + dirty_rect.size.height;
    
    // Convert pixel coordinates to cell coordinates
    // For columns: divide x by char_width
    int start_col = static_cast<int>(std::floor(grid_x / char_width));
    int end_col = static_cast<int>(std::ceil(grid_right / char_width));
    
    // For rows: need to handle CoreGraphics bottom-left origin
    // In CoreGraphics, y=0 is at bottom, increasing upward
    // In TTK, row=0 is at top, increasing downward
    // 
    // grid_y is the bottom edge of the dirty rect in grid coordinates
    // grid_top is the top edge of the dirty rect in grid coordinates
    // 
    // Convert to TTK row coordinates:
    // - Bottom edge (grid_y) corresponds to higher row numbers (bottom of grid)
    // - Top edge (grid_top) corresponds to lower row numbers (top of grid)
    
    // Calculate which TTK rows are affected
    // Row at bottom of dirty rect (highest y in CG coords)
    int bottom_row = rows - static_cast<int>(std::ceil(grid_top / char_height));
    // Row at top of dirty rect (lowest y in CG coords)
    int top_row = rows - static_cast<int>(std::floor(grid_y / char_height));
    
    // Clamp to valid grid bounds
    start_col = std::max(0, std::min(start_col, cols));
    end_col = std::max(0, std::min(end_col, cols));
    
    // For rows, start_row should be the smaller value (top of grid)
    // and end_row should be the larger value (bottom of grid)
    int start_row = std::max(0, std::min(bottom_row, rows));
    int end_row = std::max(0, std::min(top_row, rows));
    
    // Ensure start_row <= end_row
    if (start_row > end_row) {
        std::swap(start_row, end_row);
    }
    
    // Create and return CellRect
    CellRect result;
    result.start_row = start_row;
    result.end_row = end_row;
    result.start_col = start_col;
    result.end_col = end_col;
    
    return result;
}

//=============================================================================
// Forward Declarations
//=============================================================================

// Data structure parsing functions
static std::vector<std::vector<Cell>> parse_grid(PyObject* grid_obj, int expected_rows, int expected_cols);
static std::unordered_map<int, ColorPair> parse_color_pairs(PyObject* pairs_obj);

// Main rendering function
static PyObject* render_frame(PyObject* self, PyObject* args, PyObject* kwargs);

// Cache management functions
static PyObject* clear_caches(PyObject* self, PyObject* args);
static PyObject* get_performance_metrics(PyObject* self, PyObject* args);
static PyObject* reset_metrics(PyObject* self, PyObject* args);
static PyObject* enable_perf_logging(PyObject* self, PyObject* args);

// Drag-and-drop function
static PyObject* start_drag_session(PyObject* self, PyObject* args);

//=============================================================================
// Module Method Definitions
//=============================================================================

static PyMethodDef CppRendererMethods[] = {
    {
        "render_frame",
        (PyCFunction)render_frame,
        METH_VARARGS | METH_KEYWORDS,
        "Render a frame using CoreGraphics/CoreText APIs.\n\n"
        "Parameters:\n"
        "  context: CGContextRef (as Python integer/long)\n"
        "  grid: List of lists containing (char, color_pair, attributes) tuples\n"
        "  color_pairs: Dict mapping color_pair ID to ((r,g,b), (r,g,b)) tuples\n"
        "  dirty_rect: NSRect as (x, y, width, height) tuple\n"
        "  char_width: Character width in pixels (float)\n"
        "  char_height: Character height in pixels (float)\n"
        "  rows: Number of rows in grid (int)\n"
        "  cols: Number of columns in grid (int)\n"
        "  offset_x: X offset for centering (float)\n"
        "  offset_y: Y offset for centering (float)\n"
        "  cursor_visible: Whether cursor is visible (bool)\n"
        "  cursor_row: Cursor row position (int)\n"
        "  cursor_col: Cursor column position (int)\n"
        "  marked_text: IME marked text string (str or None)\n"
        "  selected_range_location: Location of selected portion within marked text (int)\n"
        "  selected_range_length: Length of selected portion within marked text (int)\n"
        "  font_ascent: Font ascent for baseline positioning (float)\n"
        "  font_names: List of font names (first is primary, rest are cascade) (list or str, optional, default=['Menlo'])\n"
        "  font_size: Font size in points (float, optional, default=12.0)\n"
    },
    {
        "clear_caches",
        clear_caches,
        METH_NOARGS,
        "Clear all internal caches (fonts, colors, attributes)."
    },
    {
        "get_performance_metrics",
        get_performance_metrics,
        METH_NOARGS,
        "Get performance metrics as a dictionary."
    },
    {
        "reset_metrics",
        reset_metrics,
        METH_NOARGS,
        "Reset performance metrics counters to zero."
    },
    {
        "enable_perf_logging",
        enable_perf_logging,
        METH_VARARGS,
        "Enable or disable performance logging to stderr.\n\n"
        "Parameters:\n"
        "  enable: Boolean - True to enable, False to disable\n\n"
        "When enabled, logs performance metrics every 60 frames including:\n"
        "  - Render time per frame\n"
        "  - Average batches per frame\n"
        "  - Average characters per frame\n"
        "  - Average batch splits per frame\n"
        "  - Font cache hit rate\n"
    },
    {
        "start_drag_session",
        (PyCFunction)start_drag_session,
        METH_VARARGS,
        "Start a native macOS drag-and-drop session.\n\n"
        "Parameters:\n"
        "  view: NSView object (as Python integer/long)\n"
        "  file_urls: List of file:// URL strings\n"
        "  drag_image_text: Text to display in drag image (str)\n"
        "  event: NSEvent object (as Python integer/long, 0 if not available)\n\n"
        "Returns:\n"
        "  bool: True if drag started successfully, False otherwise\n"
    },
    {nullptr, nullptr, 0, nullptr}  // Sentinel
};

//=============================================================================
// Module Definition
//=============================================================================

static struct PyModuleDef ttk_coregraphics_render_module = {
    PyModuleDef_HEAD_INIT,
    "ttk_coregraphics_render",                           // Module name
    "C++ rendering backend for CoreGraphics/CoreText",  // Module docstring
    -1,                                                  // Module state size
    CppRendererMethods                                   // Module methods
};

//=============================================================================
// Module Initialization
//=============================================================================

PyMODINIT_FUNC PyInit_ttk_coregraphics_render(void) {
    PyObject* module = PyModule_Create(&ttk_coregraphics_render_module);
    if (module == nullptr) {
        return nullptr;
    }
    
    // Add module version
    PyModule_AddStringConstant(module, "__version__", CPP_RENDERER_VERSION);
    
    return module;
}

//=============================================================================
// Data Structure Parsing Functions
//=============================================================================

/**
 * Parse Python grid into C++ vector structure.
 * 
 * @param grid_obj Python list of lists containing (char, color_pair, attributes) tuples
 * @param expected_rows Expected number of rows for validation
 * @param expected_cols Expected number of columns for validation
 * @return Vector of vectors containing Cell structures
 * @throws std::runtime_error if validation fails
 */
static std::vector<std::vector<Cell>> parse_grid(PyObject* grid_obj, int expected_rows, int expected_cols) {
    // Validate grid_obj is a list
    if (!PyList_Check(grid_obj)) {
        throw std::runtime_error("Grid must be a list");
    }
    
    Py_ssize_t num_rows = PyList_Size(grid_obj);
    
    // Validate number of rows
    if (num_rows != expected_rows) {
        throw std::runtime_error(
            "Grid row count mismatch: expected " + std::to_string(expected_rows) +
            ", got " + std::to_string(num_rows)
        );
    }
    
    std::vector<std::vector<Cell>> grid;
    grid.reserve(num_rows);
    
    // Iterate through rows
    for (Py_ssize_t row = 0; row < num_rows; ++row) {
        PyObject* row_obj = PyList_GetItem(grid_obj, row);  // Borrowed reference
        
        if (!PyList_Check(row_obj)) {
            throw std::runtime_error("Grid row " + std::to_string(row) + " must be a list");
        }
        
        Py_ssize_t num_cols = PyList_Size(row_obj);
        
        // Validate number of columns
        if (num_cols != expected_cols) {
            throw std::runtime_error(
                "Grid row " + std::to_string(row) + " column count mismatch: expected " +
                std::to_string(expected_cols) + ", got " + std::to_string(num_cols)
            );
        }
        
        std::vector<Cell> row_cells;
        row_cells.reserve(num_cols);
        
        // Iterate through columns
        for (Py_ssize_t col = 0; col < num_cols; ++col) {
            PyObject* cell_obj = PyList_GetItem(row_obj, col);  // Borrowed reference
            
            // Validate cell is a tuple
            if (!PyTuple_Check(cell_obj)) {
                throw std::runtime_error(
                    "Grid cell (" + std::to_string(row) + ", " + std::to_string(col) +
                    ") must be a tuple"
                );
            }
            
            // Validate tuple has 4 elements
            if (PyTuple_Size(cell_obj) != 4) {
                throw std::runtime_error(
                    "Grid cell (" + std::to_string(row) + ", " + std::to_string(col) +
                    ") must have 4 elements (char, color_pair, attributes, is_wide)"
                );
            }
            
            // Extract character (UTF-8 string from Python)
            PyObject* char_obj = PyTuple_GetItem(cell_obj, 0);  // Borrowed reference
            if (!PyUnicode_Check(char_obj)) {
                throw std::runtime_error(
                    "Grid cell (" + std::to_string(row) + ", " + std::to_string(col) +
                    ") character must be a string"
                );
            }
            
            // Convert Python Unicode string to UTF-16 (std::u16string)
            // Python 3 uses Unicode internally, so we can get UTF-16 directly
            Py_ssize_t char_length;
            const Py_UCS2* char_data = PyUnicode_2BYTE_DATA(char_obj);
            char_length = PyUnicode_GET_LENGTH(char_obj);
            
            std::u16string character;
            if (char_data != nullptr && char_length > 0) {
                // Check if Python is using UCS-2 (2-byte) representation
                if (PyUnicode_KIND(char_obj) == PyUnicode_2BYTE_KIND) {
                    character = std::u16string(reinterpret_cast<const char16_t*>(char_data), char_length);
                } else {
                    // Fallback: convert via UTF-8
                    const char* char_utf8 = PyUnicode_AsUTF8(char_obj);
                    if (char_utf8 == nullptr) {
                        throw std::runtime_error(
                            "Failed to convert character at (" + std::to_string(row) +
                            ", " + std::to_string(col) + ")"
                        );
                    }
                    // Convert UTF-8 to UTF-16
                    std::wstring_convert<std::codecvt_utf8_utf16<char16_t>, char16_t> converter;
                    character = converter.from_bytes(char_utf8);
                }
            }
            
            // Extract color_pair (integer)
            PyObject* color_pair_obj = PyTuple_GetItem(cell_obj, 1);  // Borrowed reference
            if (!PyLong_Check(color_pair_obj)) {
                throw std::runtime_error(
                    "Grid cell (" + std::to_string(row) + ", " + std::to_string(col) +
                    ") color_pair must be an integer"
                );
            }
            long color_pair = PyLong_AsLong(color_pair_obj);
            if (color_pair == -1 && PyErr_Occurred()) {
                throw std::runtime_error(
                    "Failed to convert color_pair to integer at (" + std::to_string(row) +
                    ", " + std::to_string(col) + ")"
                );
            }
            
            // Extract attributes (integer)
            PyObject* attributes_obj = PyTuple_GetItem(cell_obj, 2);  // Borrowed reference
            if (!PyLong_Check(attributes_obj)) {
                throw std::runtime_error(
                    "Grid cell (" + std::to_string(row) + ", " + std::to_string(col) +
                    ") attributes must be an integer"
                );
            }
            long attributes = PyLong_AsLong(attributes_obj);
            if (attributes == -1 && PyErr_Occurred()) {
                throw std::runtime_error(
                    "Failed to convert attributes to integer at (" + std::to_string(row) +
                    ", " + std::to_string(col) + ")"
                );
            }
            
            // Extract is_wide (boolean)
            PyObject* is_wide_obj = PyTuple_GetItem(cell_obj, 3);  // Borrowed reference
            int is_wide_result = PyObject_IsTrue(is_wide_obj);
            if (is_wide_result == -1) {
                throw std::runtime_error(
                    "Failed to convert is_wide to boolean at (" + std::to_string(row) +
                    ", " + std::to_string(col) + ")"
                );
            }
            bool is_wide = (is_wide_result == 1);
            
            // Create cell and add to row
            Cell cell;
            cell.character = std::move(character);
            cell.color_pair = static_cast<int>(color_pair);
            cell.attributes = static_cast<int>(attributes);
            cell.is_wide = is_wide;
            
            row_cells.push_back(std::move(cell));
        }
        
        grid.push_back(std::move(row_cells));
    }
    
    return grid;
}

/**
 * Parse Python color_pairs dictionary into C++ map structure.
 * 
 * @param pairs_obj Python dict mapping color_pair ID to ((r,g,b), (r,g,b)) tuples
 * @return Unordered map of color pair IDs to ColorPair structures
 * @throws std::runtime_error if validation fails
 */
static std::unordered_map<int, ColorPair> parse_color_pairs(PyObject* pairs_obj) {
    // Validate pairs_obj is a dict
    if (!PyDict_Check(pairs_obj)) {
        throw std::runtime_error("Color pairs must be a dictionary");
    }
    
    std::unordered_map<int, ColorPair> color_pairs;
    
    // Iterate through dictionary items
    PyObject* key;
    PyObject* value;
    Py_ssize_t pos = 0;
    
    while (PyDict_Next(pairs_obj, &pos, &key, &value)) {
        // Extract color pair ID (key)
        if (!PyLong_Check(key)) {
            throw std::runtime_error("Color pair ID must be an integer");
        }
        long pair_id = PyLong_AsLong(key);
        if (pair_id == -1 && PyErr_Occurred()) {
            throw std::runtime_error("Failed to convert color pair ID to integer");
        }
        
        // Validate value is a tuple with 2 elements
        if (!PyTuple_Check(value) || PyTuple_Size(value) != 2) {
            throw std::runtime_error(
                "Color pair " + std::to_string(pair_id) +
                " must be a tuple of 2 RGB tuples"
            );
        }
        
        // Extract foreground RGB tuple
        PyObject* fg_tuple = PyTuple_GetItem(value, 0);  // Borrowed reference
        if (!PyTuple_Check(fg_tuple) || PyTuple_Size(fg_tuple) != 3) {
            throw std::runtime_error(
                "Color pair " + std::to_string(pair_id) +
                " foreground must be an RGB tuple (r, g, b)"
            );
        }
        
        // Extract background RGB tuple
        PyObject* bg_tuple = PyTuple_GetItem(value, 1);  // Borrowed reference
        if (!PyTuple_Check(bg_tuple) || PyTuple_Size(bg_tuple) != 3) {
            throw std::runtime_error(
                "Color pair " + std::to_string(pair_id) +
                " background must be an RGB tuple (r, g, b)"
            );
        }
        
        // Helper lambda to extract and validate RGB values
        auto extract_rgb = [](PyObject* rgb_tuple, const std::string& context) -> uint32_t {
            uint8_t rgb[3];
            
            for (int i = 0; i < 3; ++i) {
                PyObject* component = PyTuple_GetItem(rgb_tuple, i);  // Borrowed reference
                
                if (!PyLong_Check(component)) {
                    throw std::runtime_error(context + " RGB component must be an integer");
                }
                
                long value = PyLong_AsLong(component);
                if (value == -1 && PyErr_Occurred()) {
                    throw std::runtime_error(context + " failed to convert RGB component");
                }
                
                // Validate range 0-255
                if (value < 0 || value > 255) {
                    throw std::runtime_error(
                        context + " RGB component must be in range 0-255, got " +
                        std::to_string(value)
                    );
                }
                
                rgb[i] = static_cast<uint8_t>(value);
            }
            
            // Pack into 0x00RRGGBB format
            return (static_cast<uint32_t>(rgb[0]) << 16) |
                   (static_cast<uint32_t>(rgb[1]) << 8) |
                   static_cast<uint32_t>(rgb[2]);
        };
        
        // Extract and pack RGB values
        uint32_t fg_rgb = extract_rgb(
            fg_tuple,
            "Color pair " + std::to_string(pair_id) + " foreground"
        );
        
        uint32_t bg_rgb = extract_rgb(
            bg_tuple,
            "Color pair " + std::to_string(pair_id) + " background"
        );
        
        // Create ColorPair and add to map
        ColorPair color_pair;
        color_pair.fg_rgb = fg_rgb;
        color_pair.bg_rgb = bg_rgb;
        
        color_pairs[static_cast<int>(pair_id)] = color_pair;
    }
    
    return color_pairs;
}

//=============================================================================
// Background Rendering Functions
//=============================================================================

/**
 * Render backgrounds for cells in the dirty region.
 * Accumulates adjacent cells with the same background color into batches
 * using RectangleBatcher for efficient rendering.
 * 
 * @param batcher RectangleBatcher to accumulate background rectangles
 * @param grid Parsed grid data
 * @param color_pairs Parsed color pair data
 * @param dirty_cells Cell rectangle defining the dirty region
 * @param char_width Width of each character cell in pixels
 * @param char_height Height of each character cell in pixels
 * @param rows Total number of rows in grid
 * @param cols Total number of columns in grid
 * @param offset_x X offset for centering the grid in the view
 * @param offset_y Y offset for centering the grid in the view
 */
static void render_backgrounds(
    RectangleBatcher& batcher,
    const std::vector<std::vector<Cell>>& grid,
    const std::unordered_map<int, ColorPair>& color_pairs,
    const CellRect& dirty_cells,
    CGFloat char_width,
    CGFloat char_height,
    int rows,
    int cols,
    CGFloat offset_x,
    CGFloat offset_y
) {
    // Pre-calculate edge cell boundaries for performance
    // Only edge cells need special handling for background extension
    int left_col = 0;
    int right_col = cols - 1;
    
    // Only apply edge extension if there's actual padding (offset > 0)
    // This prevents unnecessary extension when rendering without padding
    bool has_padding = (offset_x > 0.01f || offset_y > 0.01f);
    
    // Iterate through dirty region cells
    for (int row = dirty_cells.start_row; row < dirty_cells.end_row; ++row) {
        for (int col = dirty_cells.start_col; col < dirty_cells.end_col; ++col) {
            // Get cell from grid
            const Cell& cell = grid[row][col];
            
            // Skip empty cells (placeholders for wide characters)
            // These cells should not have backgrounds drawn
            if (cell.character.empty()) {
                continue;
            }
            
            // Skip variation selectors (U+FE00-U+FE0F) backgrounds
            // Variation selectors modify the preceding character's appearance
            // but should not have their own background drawn
            if (cell.character.length() == 1) {
                char16_t ch = cell.character[0];
                if (ch >= 0xFE00 && ch <= 0xFE0F) {
                    continue;
                }
            }
            
            // Get color pair for this cell
            auto color_it = color_pairs.find(cell.color_pair);
            if (color_it == color_pairs.end()) {
                // Color pair not found - skip this cell
                continue;
            }
            
            const ColorPair& colors = color_it->second;
            uint32_t bg_rgb = colors.bg_rgb;
            uint32_t fg_rgb = colors.fg_rgb;
            
            // Handle REVERSE attribute (bit 2) by swapping foreground and background
            // This is a common terminal attribute for highlighting text
            if (cell.attributes & 4) {  // REVERSE is bit 2 (value 4)
                std::swap(bg_rgb, fg_rgb);
            }
            
            // Calculate base pixel position for this cell
            // Convert TTK row to CoreGraphics y-coordinate
            CGFloat y = ttk_to_cg_y(row, rows, char_height) + offset_y;
            CGFloat x = static_cast<CGFloat>(col) * char_width + offset_x;
            
            // Determine cell width based on whether this is a wide character
            // Wide characters (zenkaku) occupy 2 grid cells
            CGFloat base_cell_width = cell.is_wide ? (char_width * 2.0f) : char_width;
            
            // Edge extension optimization: Only check edge cells when padding exists
            // For non-edge cells, use standard dimensions (fast path)
            // For edge cells with padding, calculate extended dimensions (slow path)
            bool is_edge_row = (row == 0 || row == rows - 1);
            bool is_edge_col = (col == left_col || col == right_col);
            
            if (has_padding && (is_edge_row || is_edge_col)) {
                // Slow path: Edge cell with padding - calculate extended dimensions
                // This matches the PyObjC backend behavior to fill window padding
                CGFloat cell_x = x;
                CGFloat cell_y = y;
                CGFloat cell_width = base_cell_width;
                CGFloat cell_height = char_height;
                
                // Extend left edge (leftmost column)
                if (col == left_col) {
                    cell_x = 0;
                    cell_width = base_cell_width + offset_x;
                }
                
                // Extend right edge (rightmost column)
                if (col == right_col) {
                    cell_width = base_cell_width + offset_x;
                }
                
                // Extend top edge (topmost row)
                // In CoreGraphics coordinates, top edge is at highest y value
                if (row == 0) {
                    cell_height = char_height + offset_y;
                }
                
                // Extend bottom edge (bottommost row)
                // In CoreGraphics coordinates, bottom edge is at y=0
                if (row == rows - 1) {
                    cell_y = 0;
                    cell_height = char_height + offset_y;
                }
                
                // Add extended cell to batcher
                batcher.add_cell(cell_x, cell_y, cell_width, cell_height, bg_rgb);
            } else {
                // Fast path: Interior cell or no padding - use standard dimensions
                batcher.add_cell(x, y, base_cell_width, char_height, bg_rgb);
            }
        }
        
        // Finish row to ensure batches don't span rows
        batcher.finish_row();
    }
}

/**
 * Draw batched background rectangles to the CoreGraphics context.
 * Iterates through batches from RectangleBatcher and draws each batch
 * as a filled rectangle with the appropriate color.
 * 
 * @param context CGContextRef to draw to
 * @param batcher RectangleBatcher containing the batches to draw
 * @param color_cache ColorCache for getting CGColorRef objects
 */
static void draw_batched_backgrounds(
    CGContextRef context,
    RectangleBatcher& batcher,
    ColorCache& color_cache
) {
    // Get all batches from the batcher
    const auto& batches = batcher.get_batches();
    
    // Iterate through batches and draw each one
    for (const auto& batch : batches) {
        // Extract RGB components from packed value
        uint8_t r = (batch.bg_rgb >> 16) & 0xFF;
        uint8_t g = (batch.bg_rgb >> 8) & 0xFF;
        uint8_t b = batch.bg_rgb & 0xFF;
        
        // Set fill color using CGContextSetRGBFillColor
        // This is more efficient than creating a CGColor for each batch
        CGContextSetRGBFillColor(
            context,
            r / 255.0f,
            g / 255.0f,
            b / 255.0f,
            1.0f  // Alpha = 1.0 (fully opaque)
        );
        
        // Create CGRect for the batch
        CGRect rect = CGRectMake(
            batch.x,
            batch.y,
            batch.width,
            batch.height
        );
        
        // Draw filled rectangle
        CGContextFillRect(context, rect);
    }
}

//=============================================================================
// Character Rendering Functions
//=============================================================================

/**
 * Structure representing a batch of consecutive characters with the same attributes.
 */
struct CharacterBatch {
    std::u16string text;           // UTF-16 text (compatible with UniChar)
    std::vector<bool> is_wide;     // Per-character wide flag (true if occupies 2 cells)
    int font_attributes;           // Font attributes (BOLD, etc.)
    uint32_t fg_rgb;               // Foreground color (packed RGB)
    bool underline;                // Underline flag
    CGFloat x;                     // Starting x position
    CGFloat y;                     // Starting y position
    int font_index;                // Index of font in cascade list (-1 = primary, 0+ = cascade)
};

//=============================================================================
// Performance Metrics (declared early for use in rendering functions)
//=============================================================================

static size_t g_frames_rendered = 0;
static double g_total_render_time_ms = 0.0;
static size_t g_total_batches = 0;
static size_t g_total_characters = 0;
static size_t g_total_batch_splits = 0;
static size_t g_font_lookups = 0;
static size_t g_font_cache_hits = 0;
static bool g_enable_perf_logging = false;
static char16_t g_last_failed_char = 0;  // Last character that failed font lookup

/**
 * Determine which font from the cascade list can render a character.
 * Returns the font index that can render the character.
 * Handles both single characters and surrogate pairs (e.g., emoji).
 * 
 * @param character Pointer to UTF-16 character data (may be surrogate pair)
 * @param char_length Length of character data (1 for BMP, 2 for surrogate pairs)
 * @param base_font Primary font to try first
 * @param font_attributes Font attributes (for bold trait)
 * @return Font index: -1 for primary font, 0+ for cascade font index, -2 if no font found
 */
static int get_font_index_for_character(
    const char16_t* character,
    size_t char_length,
    CTFontRef base_font,
    int font_attributes
) {
    // Track font lookups for performance metrics
    g_font_lookups++;
    
    // Handle empty character
    if (character == nullptr || char_length == 0) {
        return -2;  // No font found
    }
    
    // Convert character(s) to UniChar array for CoreText
    // This handles both single characters and surrogate pairs
    std::vector<UniChar> uni_chars(char_length);
    for (size_t i = 0; i < char_length; ++i) {
        uni_chars[i] = static_cast<UniChar>(character[i]);
    }
    
    // Allocate glyph array (same size as character array)
    std::vector<CGGlyph> glyphs(char_length);
    
    // Try primary font first
    // CTFontGetGlyphsForCharacters handles surrogate pairs correctly
    if (CTFontGetGlyphsForCharacters(base_font, uni_chars.data(), glyphs.data(), char_length)) {
        g_font_cache_hits++;  // Primary font hit
        return -1;  // Primary font can render this character
    }
    
    // Try cascade list fonts
    CTFontDescriptorRef descriptor = CTFontCopyFontDescriptor(base_font);
    if (descriptor == nullptr) {
        return -2;  // No font found
    }
    
    CFArrayRef cascade_list = (CFArrayRef)CTFontDescriptorCopyAttribute(
        descriptor,
        kCTFontCascadeListAttribute
    );
    CFRelease(descriptor);
    
    if (cascade_list == nullptr) {
        return -2;  // No cascade list
    }
    
    CFIndex cascade_count = CFArrayGetCount(cascade_list);
    int result_index = -2;  // Default: no font found
    
    // Try each font in the cascade list
    for (CFIndex i = 0; i < cascade_count; ++i) {
        CTFontDescriptorRef cascade_desc = (CTFontDescriptorRef)CFArrayGetValueAtIndex(cascade_list, i);
        
        // Create font from descriptor with same size as base font
        CGFloat font_size = CTFontGetSize(base_font);
        CTFontRef cascade_font = CTFontCreateWithFontDescriptor(
            cascade_desc,
            font_size,
            nullptr
        );
        
        if (cascade_font != nullptr) {
            // Apply bold trait if needed
            if (font_attributes & 1) {
                CTFontRef bold_cascade = CTFontCreateCopyWithSymbolicTraits(
                    cascade_font,
                    0.0,
                    nullptr,
                    kCTFontBoldTrait,
                    kCTFontBoldTrait
                );
                
                if (bold_cascade != nullptr) {
                    CFRelease(cascade_font);
                    cascade_font = bold_cascade;
                }
            }
            
            // Try to get glyph with this cascade font
            // CTFontGetGlyphsForCharacters handles surrogate pairs correctly
            if (CTFontGetGlyphsForCharacters(cascade_font, uni_chars.data(), glyphs.data(), char_length)) {
                g_font_cache_hits++;  // Cascade font hit
                result_index = static_cast<int>(i);
                CFRelease(cascade_font);
                break;  // Found a font that can render this character
            }
            
            CFRelease(cascade_font);
        }
    }
    
    CFRelease(cascade_list);
    
    return result_index;
}

/**
 * Render characters for cells in the dirty region.
 * Batches consecutive characters with the same attributes for efficient rendering.
 * Skips spaces (backgrounds already rendered) and handles wide characters.
 * 
 * @param context CGContextRef to draw to
 * @param grid Parsed grid data
 * @param color_pairs Parsed color pair data
 * @param dirty_cells Cell rectangle defining the dirty region
 * @param char_width Width of each character cell in pixels
 * @param char_height Height of each character cell in pixels
 * @param rows Total number of rows in grid
 * @param cols Total number of columns in grid
 * @param offset_x X offset for centering the grid in the view
 * @param offset_y Y offset for centering the grid in the view
 * @param font_ascent Font ascent for baseline positioning
 * @param attr_dict_cache AttributeDictCache for getting attribute dictionaries
 */
static void render_characters(
    CGContextRef context,
    const std::vector<std::vector<Cell>>& grid,
    const std::unordered_map<int, ColorPair>& color_pairs,
    const CellRect& dirty_cells,
    CGFloat char_width,
    CGFloat char_height,
    int rows,
    int cols,
    CGFloat offset_x,
    CGFloat offset_y,
    CGFloat font_ascent,
    AttributeDictCache& attr_dict_cache
);

// Forward declaration for draw_character_batch
static void draw_character_batch(
    CGContextRef context,
    const CharacterBatch& batch,
    CGFloat char_width,
    CGFloat char_height,
    CGFloat font_ascent,
    AttributeDictCache& attr_dict_cache
);

/**
 * Draw a batch of characters with the same attributes.
 * Uses CGContextShowGlyphsAtPositions to render glyphs at exact grid positions,
 * ensuring proper monospace alignment regardless of font metrics.
 * 
 * @param context CGContextRef to draw to
 * @param batch CharacterBatch containing the text and attributes to draw
 * @param char_width Width of each character cell in pixels
 * @param char_height Height of each character cell in pixels
 * @param font_ascent Font ascent for baseline positioning
 * @param attr_dict_cache AttributeDictCache for getting attribute dictionaries
 */
static void draw_character_batch(
    CGContextRef context,
    const CharacterBatch& batch,
    CGFloat char_width,
    CGFloat char_height,
    CGFloat font_ascent,
    AttributeDictCache& attr_dict_cache
) {
    // Get font and color from attribute dictionary
    CFDictionaryRef attributes = attr_dict_cache.get_attributes(
        batch.font_attributes,
        batch.fg_rgb,
        batch.underline
    );
    
    if (attributes == nullptr) {
        return;
    }
    
    // Extract base font from attributes
    CTFontRef base_font = (CTFontRef)CFDictionaryGetValue(
        attributes, 
        kCTFontAttributeName
    );
    
    if (base_font == nullptr) {
        return;
    }
    
    // Extract color from attributes
    CGColorRef color = (CGColorRef)CFDictionaryGetValue(
        attributes, 
        kCTForegroundColorAttributeName
    );
    
    if (color == nullptr) {
        return;
    }
    
    // Convert UTF-16 string to UniChar array for glyph lookup
    // Since char16_t and UniChar are both 16-bit, we can directly copy
    CFIndex length = static_cast<CFIndex>(batch.text.length());
    if (length == 0) {
        return;
    }
    
    // Allocate arrays for characters, glyphs, and positions
    std::vector<UniChar> characters(length);
    std::vector<CGGlyph> glyphs(length);
    std::vector<CGPoint> positions(length);
    
    // Copy UTF-16 characters directly to UniChar array
    for (CFIndex i = 0; i < length; ++i) {
        characters[i] = static_cast<UniChar>(batch.text[i]);
    }
    
    // Determine which font to use based on batch.font_index
    CTFontRef font_to_use = base_font;
    CTFontRef allocated_font = nullptr;
    
    if (batch.font_index == -1) {
        // Use primary font
        font_to_use = base_font;
    } else if (batch.font_index >= 0) {
        // Use cascade font at specified index
        CTFontDescriptorRef descriptor = CTFontCopyFontDescriptor(base_font);
        if (descriptor != nullptr) {
            CFArrayRef cascade_list = (CFArrayRef)CTFontDescriptorCopyAttribute(
                descriptor,
                kCTFontCascadeListAttribute
            );
            CFRelease(descriptor);
            
            if (cascade_list != nullptr) {
                CFIndex cascade_count = CFArrayGetCount(cascade_list);
                
                if (batch.font_index < cascade_count) {
                    CTFontDescriptorRef cascade_desc = (CTFontDescriptorRef)CFArrayGetValueAtIndex(
                        cascade_list, 
                        batch.font_index
                    );
                    
                    // Create font from descriptor with same size as base font
                    CGFloat font_size = CTFontGetSize(base_font);
                    CTFontRef cascade_font = CTFontCreateWithFontDescriptor(
                        cascade_desc,
                        font_size,
                        nullptr
                    );
                    
                    if (cascade_font != nullptr) {
                        // Apply bold trait if needed
                        CTFontSymbolicTraits base_traits = CTFontGetSymbolicTraits(base_font);
                        if (base_traits & kCTFontBoldTrait) {
                            CTFontRef bold_cascade = CTFontCreateCopyWithSymbolicTraits(
                                cascade_font,
                                0.0,
                                nullptr,
                                kCTFontBoldTrait,
                                kCTFontBoldTrait
                            );
                            
                            if (bold_cascade != nullptr) {
                                CFRelease(cascade_font);
                                cascade_font = bold_cascade;
                            }
                        }
                        
                        allocated_font = cascade_font;
                        font_to_use = cascade_font;
                    }
                }
                
                CFRelease(cascade_list);
            }
        }
    }
    
    // Get glyphs for characters using the selected font
    bool all_glyphs_found = CTFontGetGlyphsForCharacters(
        font_to_use, 
        characters.data(), 
        glyphs.data(), 
        length
    );
    
    // If glyphs not found with selected font, skip rendering
    if (!all_glyphs_found) {
        if (allocated_font != nullptr) {
            CFRelease(allocated_font);
        }
        return;
    }
    
    // Count actual glyphs (surrogate pairs become single glyphs)
    // CTFontGetGlyphsForCharacters converts surrogate pairs to single glyphs,
    // leaving 0 in the second position
    CFIndex actual_glyph_count = 0;
    for (CFIndex i = 0; i < length; ++i) {
        if (glyphs[i] != 0) {
            actual_glyph_count++;
        }
    }
    
    // If no valid glyphs, skip rendering
    if (actual_glyph_count == 0) {
        if (allocated_font != nullptr) {
            CFRelease(allocated_font);
        }
        return;
    }
    
    // Calculate baseline position
    CGFloat baseline_y = batch.y + (char_height - font_ascent);
    
    // Get actual glyph advances from the font
    // This is critical for proper character spacing
    // Note: We get advances for all positions, but only use the valid ones
    std::vector<CGSize> advances(length);
    CTFontGetAdvancesForGlyphs(
        font_to_use,
        kCTFontOrientationHorizontal,
        glyphs.data(),
        advances.data(),
        length
    );
    
    // Build arrays of valid glyphs and their positions
    std::vector<CGGlyph> valid_glyphs;
    std::vector<CGPoint> valid_positions;
    valid_glyphs.reserve(actual_glyph_count);
    valid_positions.reserve(actual_glyph_count);
    
    // Calculate position for each valid glyph
    CGFloat x = batch.x;
    size_t is_wide_index = 0;
    
    for (CFIndex i = 0; i < length; ++i) {
        // Skip invalid glyphs (0 means no glyph, typically second half of surrogate pair)
        if (glyphs[i] == 0) {
            continue;
        }
        
        // Get the actual glyph advance width
        CGFloat glyph_advance = advances[i].width;
        
        // Check if this character is wide (occupies 2 cells)
        bool char_is_wide = (is_wide_index < batch.is_wide.size()) ? batch.is_wide[is_wide_index] : false;
        CGFloat cell_width = char_is_wide ? (char_width * 2.0f) : char_width;
        
        // Center the glyph within its cell(s) for better visual alignment
        CGFloat centering_offset = (cell_width - glyph_advance) / 2.0f;
        
        CGPoint pos;
        pos.x = x + centering_offset;
        pos.y = baseline_y;
        
        valid_glyphs.push_back(glyphs[i]);
        valid_positions.push_back(pos);
        
        // Advance by the cell width (not glyph advance) to maintain grid alignment
        x += cell_width;
        is_wide_index++;
    }
    
    // Set fill color for text
    CGContextSetFillColorWithColor(context, color);
    
    // Check if we need synthetic bold (cascade font with bold attribute)
    bool use_synthetic_bold = false;
    if (allocated_font != nullptr && (batch.font_attributes & 1)) {
        // We're using a cascade font and bold was requested
        // Check if the cascade font actually has the bold trait
        CTFontSymbolicTraits cascade_traits = CTFontGetSymbolicTraits(font_to_use);
        if (!(cascade_traits & kCTFontBoldTrait)) {
            // Cascade font doesn't have bold trait, use synthetic bold
            use_synthetic_bold = true;
        }
    }
    
    // Set text drawing mode
    if (use_synthetic_bold) {
        // Use fill and stroke for synthetic bold
        CGContextSetTextDrawingMode(context, kCGTextFillStroke);
        CGContextSetLineWidth(context, 0.5);  // Stroke width for synthetic bold
        CGContextSetStrokeColorWithColor(context, color);
    } else {
        // Normal fill mode
        CGContextSetTextDrawingMode(context, kCGTextFill);
    }
    
    // Enable anti-aliasing for smooth rendering
    CGContextSetShouldAntialias(context, true);
    CGContextSetShouldSmoothFonts(context, true);
    
    // Get CGFont from CTFont for glyph rendering
    CGFontRef cg_font = CTFontCopyGraphicsFont(font_to_use, nullptr);
    if (cg_font != nullptr) {
        CGContextSetFont(context, cg_font);
        CGContextSetFontSize(context, CTFontGetSize(font_to_use));
        CFRelease(cg_font);
    } else {
        if (allocated_font != nullptr) {
            CFRelease(allocated_font);
        }
        return;
    }
    
    // Draw glyphs at exact positions
    // Use CTFontDrawGlyphs instead of CGContextShowGlyphsAtPositions
    // CTFontDrawGlyphs properly renders color emoji, while CGContextShowGlyphsAtPositions
    // only renders glyph outlines (causing emoji to appear in grayscale)
    // CRITICAL: Use valid_glyphs and valid_positions (filtered to remove 0 glyphs from surrogate pairs)
    CTFontDrawGlyphs(
        font_to_use,
        valid_glyphs.data(),
        valid_positions.data(),
        actual_glyph_count,
        context
    );
    
    // Draw underline if needed
    if (batch.underline) {
        // Position underline between the text baseline and bottom of the text grid row
        // This provides better visual balance than positioning at the very bottom
        // baseline_y is where the text sits, batch.y is the bottom of the cell
        // Position underline midway between them
        CGFloat underline_thickness = CTFontGetUnderlineThickness(font_to_use);
        CGFloat underline_position = (baseline_y + batch.y) / 2.0f;
        
        // Draw underline as a filled rectangle
        // Use the actual batch width (sum of cell widths) for underline
        CGFloat underline_width = 0;
        for (size_t i = 0; i < batch.is_wide.size(); ++i) {
            underline_width += batch.is_wide[i] ? (char_width * 2.0f) : char_width;
        }
        CGContextFillRect(
            context,
            CGRectMake(batch.x, underline_position, underline_width, underline_thickness)
        );
    }
    
    // Clean up allocated font if we created one
    if (allocated_font != nullptr) {
        CFRelease(allocated_font);
    }
}

/**
 * Render characters for cells in the dirty region.
 * Implementation of the function declared above.
 */
static void render_characters(
    CGContextRef context,
    const std::vector<std::vector<Cell>>& grid,
    const std::unordered_map<int, ColorPair>& color_pairs,
    const CellRect& dirty_cells,
    CGFloat char_width,
    CGFloat char_height,
    int rows,
    int cols,
    CGFloat offset_x,
    CGFloat offset_y,
    CGFloat font_ascent,
    AttributeDictCache& attr_dict_cache
) {
    // Current batch being accumulated
    std::optional<CharacterBatch> current_batch;
    
    // Iterate through dirty region cells
    for (int row = dirty_cells.start_row; row < dirty_cells.end_row; ++row) {
        for (int col = dirty_cells.start_col; col < dirty_cells.end_col; ++col) {
            // Get cell from grid
            const Cell& cell = grid[row][col];
            
            // Skip empty cells (placeholders for wide characters) and spaces
            if (cell.character.empty()) {
                // Finish current batch if any
                if (current_batch.has_value()) {
                    draw_character_batch(context, current_batch.value(), char_width, char_height, font_ascent, attr_dict_cache);
                    current_batch = std::nullopt;
                }
                continue;
            }
            
            // Check if this is a space character
            bool is_space = (cell.character.length() == 1 && cell.character[0] == u' ');
            
            // Extract underline attribute early to decide if we should skip spaces
            bool has_underline = (cell.attributes & 2) != 0;  // UNDERLINE is bit 1
            
            // Skip spaces only if they don't have underline - backgrounds already rendered
            // If space has underline, we need to include it in the batch to draw underline
            if (is_space && !has_underline) {
                // Finish current batch if any
                if (current_batch.has_value()) {
                    draw_character_batch(context, current_batch.value(), char_width, char_height, font_ascent, attr_dict_cache);
                    current_batch = std::nullopt;
                }
                continue;
            }
            
            // Check if next cell is a variation selector and combine them
            // Variation selectors (U+FE00-U+FE0F) modify the preceding character
            // For proper font lookup, we need to pass them together
            std::u16string combined_char = cell.character;
            int cols_to_skip = 0;
            bool has_variation_selector = false;
            
            if (col + 1 < dirty_cells.end_col && col + 1 < cols) {
                const Cell& next_cell = grid[row][col + 1];
                if (next_cell.character.length() == 1) {
                    char16_t next_ch = next_cell.character[0];
                    if (next_ch >= 0xFE00 && next_ch <= 0xFE0F) {
                        // Next cell is a variation selector - combine it
                        combined_char += next_cell.character;
                        cols_to_skip = 1;  // Skip the variation selector cell in next iteration
                        has_variation_selector = true;  // Track that we combined with variation selector
                    }
                }
            }
            
            // Get color pair for this cell
            auto color_it = color_pairs.find(cell.color_pair);
            if (color_it == color_pairs.end()) {
                // Color pair not found - skip this cell
                if (current_batch.has_value()) {
                    draw_character_batch(context, current_batch.value(), char_width, char_height, font_ascent, attr_dict_cache);
                    current_batch = std::nullopt;
                }
                continue;
            }
            
            const ColorPair& colors = color_it->second;
            uint32_t fg_rgb = colors.fg_rgb;
            uint32_t bg_rgb = colors.bg_rgb;
            
            // Handle REVERSE attribute (bit 2) by swapping foreground and background
            // This is a common terminal attribute for highlighting text
            if (cell.attributes & 4) {  // REVERSE is bit 2 (value 4)
                std::swap(fg_rgb, bg_rgb);
            }
            
            // Extract attributes
            int font_attributes = cell.attributes & 1;  // BOLD is bit 0
            bool underline = (cell.attributes & 2) != 0;  // UNDERLINE is bit 1
            
            // Calculate pixel position for this cell
            // Convert TTK row to CoreGraphics y-coordinate
            CGFloat y = ttk_to_cg_y(row, rows, char_height) + offset_y;
            CGFloat x = static_cast<CGFloat>(col) * char_width + offset_x;
            
            // Determine which font can render this character
            // Get base font from attribute cache
            CFDictionaryRef attributes = attr_dict_cache.get_attributes(
                font_attributes,
                fg_rgb,
                false  // underline doesn't affect font selection
            );
            
            CTFontRef base_font = nullptr;
            if (attributes != nullptr) {
                base_font = (CTFontRef)CFDictionaryGetValue(
                    attributes,
                    kCTFontAttributeName
                );
            }
            
            int font_index = -2;  // Default: no font found
            if (base_font != nullptr && !combined_char.empty()) {
                font_index = get_font_index_for_character(
                    combined_char.data(),
                    combined_char.length(),
                    base_font,
                    font_attributes
                );
            }
            
            // Skip character if no font can render it
            if (font_index == -2) {
                // Finish current batch if any
                if (current_batch.has_value()) {
                    draw_character_batch(context, current_batch.value(), char_width, char_height, font_ascent, attr_dict_cache);
                    current_batch = std::nullopt;
                }
                // Skip the variation selector cell if we combined it
                col += cols_to_skip;
                continue;
            }
            
            // Check if we can extend the current batch
            bool can_extend = false;
            if (current_batch.has_value()) {
                CharacterBatch& batch = current_batch.value();
                
                // Can extend if:
                // 1. Same row (y coordinate matches)
                // 2. Same attributes (font, color, underline)
                // 3. Adjacent position (x is at the right edge of current batch)
                // 4. Same font index (same font from cascade list)
                bool same_row = (std::abs(batch.y - y) < 0.01f);
                bool same_attributes = (batch.font_attributes == font_attributes &&
                                       batch.fg_rgb == fg_rgb &&
                                       batch.underline == underline);
                
                // Calculate expected x position for next character
                // With UTF-16, we can directly iterate through characters
                CGFloat expected_x = batch.x;
                for (size_t i = 0; i < batch.text.length(); ++i) {
                    // Add width (double for wide characters)
                    bool char_is_wide = (i < batch.is_wide.size()) ? batch.is_wide[i] : false;
                    if (char_is_wide) {
                        expected_x += char_width * 2.0f;
                    } else {
                        expected_x += char_width;
                    }
                }
                
                bool adjacent = (std::abs(expected_x - x) < 0.01f);
                
                // Check if font index matches (same font from cascade)
                bool same_font = (batch.font_index == font_index);
                
                can_extend = same_row && same_attributes && adjacent && same_font;
            }
            
            if (can_extend) {
                // Extend current batch
                current_batch.value().text += combined_char;
                // If we combined with variation selector, treat as wide (occupies 2 cells)
                // Otherwise use the cell's is_wide flag
                current_batch.value().is_wide.push_back(has_variation_selector ? true : cell.is_wide);
                g_total_characters++;
            } else {
                // Finish current batch if any
                if (current_batch.has_value()) {
                    draw_character_batch(context, current_batch.value(), char_width, char_height, font_ascent, attr_dict_cache);
                    g_total_batches++;
                    
                    // Track batch split if we're starting a new batch (not just finishing at row end)
                    if (!combined_char.empty()) {
                        g_total_batch_splits++;
                    }
                }
                
                // Start new batch
                CharacterBatch new_batch;
                new_batch.text = combined_char;
                // If we combined with variation selector, treat as wide (occupies 2 cells)
                // Otherwise use the cell's is_wide flag
                new_batch.is_wide.push_back(has_variation_selector ? true : cell.is_wide);
                new_batch.font_attributes = font_attributes;
                new_batch.fg_rgb = fg_rgb;
                new_batch.underline = underline;
                new_batch.x = x;
                new_batch.y = y;
                new_batch.font_index = font_index;  // Store which font to use
                
                current_batch = new_batch;
                g_total_characters++;
            }
            
            // Skip the variation selector cell if we combined it
            col += cols_to_skip;
            
            // If this is a wide character, skip the next column (placeholder cell)
            // The next column should be a placeholder, so we'll skip it in the next iteration
            if (!cell.character.empty() && cell.is_wide) {
                // Wide character handling - placeholder will be skipped automatically
            }
        }
        
        // Finish batch at end of row
        if (current_batch.has_value()) {
            draw_character_batch(context, current_batch.value(), char_width, char_height, font_ascent, attr_dict_cache);
            g_total_batches++;
            current_batch = std::nullopt;
        }
    }
    
    // Finish any remaining batch
    if (current_batch.has_value()) {
        draw_character_batch(context, current_batch.value(), char_width, char_height, font_ascent, attr_dict_cache);
        g_total_batches++;
    }
}

//=============================================================================
// Cursor Rendering Functions
//=============================================================================

/**
 * Render the cursor at the specified position.
 * Draws a semi-transparent white filled rectangle at the cursor position
 * if the cursor is visible.
 * 
 * @param context CGContextRef to draw to
 * @param cursor_visible Whether the cursor should be rendered
 * @param cursor_row Cursor row position (TTK coordinates)
 * @param cursor_col Cursor column position (TTK coordinates)
 * @param char_width Width of each character cell in pixels
 * @param char_height Height of each character cell in pixels
 * @param rows Total number of rows in grid
 * @param offset_x X offset for centering the grid in the view
 * @param offset_y Y offset for centering the grid in the view
 */
static void render_cursor(
    CGContextRef context,
    bool cursor_visible,
    int cursor_row,
    int cursor_col,
    CGFloat char_width,
    CGFloat char_height,
    int rows,
    CGFloat offset_x,
    CGFloat offset_y
) {
    // Check cursor_visible flag - if not visible, do nothing
    if (!cursor_visible) {
        return;
    }
    
    // Calculate cursor pixel position
    // Convert TTK row to CoreGraphics y-coordinate
    CGFloat y = ttk_to_cg_y(cursor_row, rows, char_height) + offset_y;
    CGFloat x = static_cast<CGFloat>(cursor_col) * char_width + offset_x;
    
    // Set fill color to semi-transparent white
    // Using RGBA: (1.0, 1.0, 1.0, 0.5) for 50% transparent white
    CGContextSetRGBFillColor(context, 1.0f, 1.0f, 1.0f, 0.5f);
    
    // Create CGRect for the cursor
    CGRect cursor_rect = CGRectMake(x, y, char_width, char_height);
    
    // Draw filled rectangle
    CGContextFillRect(context, cursor_rect);
}

//=============================================================================
// IME Marked Text Rendering Functions
//=============================================================================

/**
 * Render IME marked text (composition text) at the cursor position.
 * Draws the marked text with background rectangles and an underline to indicate it's being composed.
 * The selected portion within marked text gets a different background color.
 * Uses the same font cascade and glyph layout logic as regular text rendering.
 * If marked_text is empty or null, no rendering is performed.
 * 
 * @param context CGContextRef to draw to
 * @param marked_text UTF-8 encoded marked text string (can be nullptr or empty)
 * @param cursor_row Cursor row position where marked text should appear
 * @param cursor_col Cursor column position where marked text should appear
 * @param char_width Width of each character cell in pixels
 * @param char_height Height of each character cell in pixels
 * @param rows Total number of rows in grid
 * @param offset_x X offset for centering the grid in the view
 * @param offset_y Y offset for centering the grid in the view
 * @param font_ascent Font ascent for baseline positioning
 * @param base_font Base CTFontRef to use for rendering (with cascade list)
 * @param color_cache ColorCache for getting foreground color
 * @param selected_range_location Location of selected portion within marked text
 * @param selected_range_length Length of selected portion within marked text
 */
static void render_marked_text(
    CGContextRef context,
    const char* marked_text,
    int cursor_row,
    int cursor_col,
    CGFloat char_width,
    CGFloat char_height,
    int rows,
    CGFloat offset_x,
    CGFloat offset_y,
    CGFloat font_ascent,
    CTFontRef base_font,
    ColorCache& color_cache,
    int selected_range_location,
    int selected_range_length
) {
    // Check if marked_text is non-empty
    if (marked_text == nullptr || marked_text[0] == '\0') {
        // No marked text to render
        return;
    }
    
    // Calculate position at cursor location
    // Convert TTK row to CoreGraphics y-coordinate
    CGFloat y = ttk_to_cg_y(cursor_row, rows, char_height) + offset_y;
    CGFloat x = static_cast<CGFloat>(cursor_col) * char_width + offset_x;
    
    // Convert UTF-8 marked text to UTF-16 for CoreText
    CFStringRef text_string = CFStringCreateWithCString(
        kCFAllocatorDefault,
        marked_text,
        kCFStringEncodingUTF8
    );
    
    if (text_string == nullptr) {
        // Failed to create CFString - cannot render
        return;
    }
    
    // Get the length of the marked text in characters
    CFIndex length = CFStringGetLength(text_string);
    if (length == 0) {
        CFRelease(text_string);
        return;
    }
    
    // Convert to UniChar array for glyph lookup
    std::vector<UniChar> characters(length);
    CFStringGetCharacters(text_string, CFRangeMake(0, length), characters.data());
    
    // Allocate arrays for glyphs and positions
    std::vector<CGGlyph> glyphs(length);
    std::vector<CGPoint> positions(length);
    
    // Get glyphs for characters using font cascade
    bool all_glyphs_found = CTFontGetGlyphsForCharacters(base_font, characters.data(), glyphs.data(), length);
    
    CTFontRef font_to_use = base_font;
    CTFontRef fallback_font = nullptr;
    
    if (!all_glyphs_found) {
        // Some glyphs are missing - try cascade list fonts
        CTFontDescriptorRef descriptor = CTFontCopyFontDescriptor(base_font);
        if (descriptor != nullptr) {
            CFArrayRef cascade_list = (CFArrayRef)CTFontDescriptorCopyAttribute(
                descriptor,
                kCTFontCascadeListAttribute
            );
            CFRelease(descriptor);
            
            if (cascade_list != nullptr) {
                CFIndex cascade_count = CFArrayGetCount(cascade_list);
                
                // Try each font in the cascade list
                for (CFIndex i = 0; i < cascade_count && !all_glyphs_found; ++i) {
                    CTFontDescriptorRef cascade_desc = (CTFontDescriptorRef)CFArrayGetValueAtIndex(cascade_list, i);
                    
                    // Create font from descriptor with same size as base font
                    CGFloat font_size = CTFontGetSize(base_font);
                    CTFontRef cascade_font = CTFontCreateWithFontDescriptor(
                        cascade_desc,
                        font_size,
                        nullptr
                    );
                    
                    if (cascade_font != nullptr) {
                        // Try to get glyphs with this cascade font
                        if (CTFontGetGlyphsForCharacters(cascade_font, characters.data(), glyphs.data(), length)) {
                            all_glyphs_found = true;
                            fallback_font = cascade_font;
                            font_to_use = fallback_font;
                        } else {
                            CFRelease(cascade_font);
                        }
                    }
                }
                
                CFRelease(cascade_list);
            }
        }
        
        // If still not found, skip rendering
        if (!all_glyphs_found) {
            CFRelease(text_string);
            return;
        }
    }
    
    // Get actual glyph advances from the font
    std::vector<CGSize> advances(length);
    CTFontGetAdvancesForGlyphs(
        font_to_use,
        kCTFontOrientationHorizontal,
        glyphs.data(),
        advances.data(),
        length
    );
    
    // Save graphics state before drawing
    CGContextSaveGState(context);
    
    // Draw background rectangles for marked text
    // Use dark gray background for unselected portions: RGB(60, 60, 60)
    // Use lighter gray background for selected portion: RGB(100, 100, 100)
    CGColorRef unselected_bg_color = color_cache.get_color(60, 60, 60, 1.0f);
    CGColorRef selected_bg_color = color_cache.get_color(100, 100, 100, 1.0f);
    
    if (unselected_bg_color != nullptr && selected_bg_color != nullptr) {
        CGFloat bg_x = x;
        
        // Draw background for each character position
        for (CFIndex i = 0; i < length; ++i) {
            // Determine if this character is in the selected range
            bool is_selected = (i >= selected_range_location && 
                              i < selected_range_location + selected_range_length);
            
            // Choose background color based on selection
            CGColorRef bg_color = is_selected ? selected_bg_color : unselected_bg_color;
            
            // Check if this is a wide character (CJK, etc.)
            // Use East Asian Width property to determine width
            bool is_wide = false;
            UniChar ch = characters[i];
            if (ch >= 0x1100) {  // Quick check for potential wide characters
                // For simplicity, check common CJK ranges
                // Full width: 0x3000-0x9FFF (CJK), 0xAC00-0xD7AF (Hangul), 0xFF00-0xFFEF (Fullwidth)
                is_wide = (ch >= 0x3000 && ch <= 0x9FFF) ||
                         (ch >= 0xAC00 && ch <= 0xD7AF) ||
                         (ch >= 0xFF00 && ch <= 0xFFEF);
            }
            
            CGFloat cell_width = is_wide ? (char_width * 2.0f) : char_width;
            
            // Calculate rectangle for this character
            CGRect bg_rect = CGRectMake(bg_x, y, cell_width, char_height);
            
            // Fill the background rectangle
            CGContextSetFillColorWithColor(context, bg_color);
            CGContextFillRect(context, bg_rect);
            
            bg_x += cell_width;
        }
    }
    
    // Calculate baseline position
    CGFloat baseline_y = y + (char_height - font_ascent);
    
    // Calculate position for each glyph using actual advances
    CGFloat glyph_x = x;
    
    for (CFIndex i = 0; i < length; ++i) {
        // Get the actual glyph advance width
        CGFloat glyph_advance = advances[i].width;
        
        // Check if this is a wide character
        bool is_wide = false;
        UniChar ch = characters[i];
        if (ch >= 0x1100) {
            is_wide = (ch >= 0x3000 && ch <= 0x9FFF) ||
                     (ch >= 0xAC00 && ch <= 0xD7AF) ||
                     (ch >= 0xFF00 && ch <= 0xFFEF);
        }
        
        CGFloat cell_width = is_wide ? (char_width * 2.0f) : char_width;
        
        // Center the glyph within its cell(s)
        CGFloat centering_offset = (cell_width - glyph_advance) / 2.0f;
        
        positions[i].x = glyph_x + centering_offset;
        positions[i].y = baseline_y;
        
        // Advance by the cell width to maintain grid alignment
        glyph_x += cell_width;
    }
    
    // Get white color for marked text (standard IME appearance)
    CGColorRef text_color = color_cache.get_color(255, 255, 255, 1.0f);
    
    if (text_color == nullptr) {
        if (fallback_font != nullptr) {
            CFRelease(fallback_font);
        }
        CFRelease(text_string);
        CGContextRestoreGState(context);
        return;
    }
    
    // Set fill color for text
    CGContextSetFillColorWithColor(context, text_color);
    
    // Set text drawing mode
    CGContextSetTextDrawingMode(context, kCGTextFill);
    
    // Enable anti-aliasing for smooth text
    CGContextSetShouldAntialias(context, true);
    CGContextSetShouldSmoothFonts(context, true);
    
    // Draw glyphs using CTFontDrawGlyphs for proper rendering
    CTFontDrawGlyphs(
        font_to_use,
        glyphs.data(),
        positions.data(),
        length,
        context
    );
    
    // Draw underline to indicate composition
    // Underline should be below the text baseline
    CGFloat underline_y = baseline_y - 2.0f;  // 2 pixels below baseline
    CGFloat underline_width = glyph_x - x;    // Total width of marked text
    
    CGContextSetStrokeColorWithColor(context, text_color);
    CGContextSetLineWidth(context, 1.0f);
    CGContextMoveToPoint(context, x, underline_y);
    CGContextAddLineToPoint(context, x + underline_width, underline_y);
    CGContextStrokePath(context);
    
    // Restore graphics state
    CGContextRestoreGState(context);
    
    // Release resources
    if (fallback_font != nullptr) {
        CFRelease(fallback_font);
    }
    CFRelease(text_string);
}

//=============================================================================
// Global State for Caches
//=============================================================================

// Global caches (initialized on first use)
static ColorCache* g_color_cache = nullptr;
static FontCache* g_font_cache = nullptr;
static AttributeDictCache* g_attr_dict_cache = nullptr;
static CTFontRef g_base_font = nullptr;

/**
 * Initialize global caches if not already initialized.
 * Creates the base font and all cache objects.
 * 
 * @param font_names_obj Python list of font names (first is primary, rest are cascade)
 * @param font_size_val Font size in points
 * @throws std::runtime_error if initialization fails
 */
static void initialize_caches(PyObject* font_names_obj, double font_size_val = 12.0) {
    // Extract font names from Python list
    std::vector<std::string> font_names;
    
    if (PyList_Check(font_names_obj)) {
        Py_ssize_t list_size = PyList_Size(font_names_obj);
        for (Py_ssize_t i = 0; i < list_size; ++i) {
            PyObject* item = PyList_GetItem(font_names_obj, i);
            if (PyUnicode_Check(item)) {
                const char* font_name_str = PyUnicode_AsUTF8(item);
                if (font_name_str != nullptr) {
                    font_names.push_back(font_name_str);
                }
            }
        }
    } else if (PyUnicode_Check(font_names_obj)) {
        // Single string for backward compatibility
        const char* font_name_str = PyUnicode_AsUTF8(font_names_obj);
        if (font_name_str != nullptr) {
            font_names.push_back(font_name_str);
        }
    }
    
    if (font_names.empty()) {
        // Fallback to default
        font_names.push_back("Menlo");
    }
    
    // Check if we need to reinitialize due to font change
    static std::vector<std::string> last_font_names;
    static double last_font_size = 0.0;
    
    bool need_reinit = (g_color_cache == nullptr) ||
                       (last_font_names != font_names) ||
                       (std::abs(last_font_size - font_size_val) > 0.01);
    
    if (!need_reinit) {
        // Already initialized with same fonts
        return;
    }
    
    // Clean up existing resources if reinitializing
    if (g_attr_dict_cache != nullptr) {
        delete g_attr_dict_cache;
        g_attr_dict_cache = nullptr;
    }
    if (g_font_cache != nullptr) {
        delete g_font_cache;
        g_font_cache = nullptr;
    }
    if (g_color_cache != nullptr) {
        delete g_color_cache;
        g_color_cache = nullptr;
    }
    if (g_base_font != nullptr) {
        CFRelease(g_base_font);
        g_base_font = nullptr;
    }
    
    // Update tracking variables
    last_font_names = font_names;
    last_font_size = font_size_val;
    
    // First font is the primary font
    const char* primary_font_name = font_names[0].c_str();
    
    // Create base font
    CFStringRef font_name = CFStringCreateWithCString(
        kCFAllocatorDefault,
        primary_font_name,
        kCFStringEncodingUTF8
    );
    
    if (font_name == nullptr) {
        throw std::runtime_error("Failed to create font name CFString");
    }
    
    CGFloat font_size = static_cast<CGFloat>(font_size_val);
    
    // Create font descriptor with cascade list
    // Remaining fonts in the list become cascade fonts
    CFMutableArrayRef cascade_descriptors = nullptr;
    
    if (font_names.size() > 1) {
        cascade_descriptors = CFArrayCreateMutable(
            kCFAllocatorDefault,
            font_names.size() - 1,
            &kCFTypeArrayCallBacks
        );
        
        if (cascade_descriptors != nullptr) {
            // Add remaining fonts as cascade fonts
            for (size_t i = 1; i < font_names.size(); ++i) {
                CFStringRef cascade_name = CFStringCreateWithCString(
                    kCFAllocatorDefault,
                    font_names[i].c_str(),
                    kCFStringEncodingUTF8
                );
                
                if (cascade_name != nullptr) {
                    CFStringRef keys[] = { kCTFontNameAttribute };
                    CFTypeRef values[] = { cascade_name };
                    
                    CFDictionaryRef attrs = CFDictionaryCreate(
                        kCFAllocatorDefault,
                        (const void**)keys,
                        (const void**)values,
                        1,
                        &kCFTypeDictionaryKeyCallBacks,
                        &kCFTypeDictionaryValueCallBacks
                    );
                    
                    CFRelease(cascade_name);
                    
                    if (attrs != nullptr) {
                        CTFontDescriptorRef desc = CTFontDescriptorCreateWithAttributes(attrs);
                        CFRelease(attrs);
                        
                        if (desc != nullptr) {
                            CFArrayAppendValue(cascade_descriptors, desc);
                            CFRelease(desc);
                        }
                    }
                }
            }
        }
    }
    
    // Create font descriptor with cascade list attribute (if we have cascade fonts)
    CTFontDescriptorRef descriptor = nullptr;
    
    if (cascade_descriptors != nullptr && CFArrayGetCount(cascade_descriptors) > 0) {
        // First create the primary font by name
        CTFontRef primary_font = CTFontCreateWithName(font_name, font_size, nullptr);
        
        if (primary_font != nullptr) {
            // Get the primary font's descriptor
            CTFontDescriptorRef primary_descriptor = CTFontCopyFontDescriptor(primary_font);
            CFRelease(primary_font);
            
            if (primary_descriptor != nullptr) {
                // Create a new descriptor by adding the cascade list to the primary font's descriptor
                CFStringRef keys[] = { kCTFontCascadeListAttribute };
                CFTypeRef values[] = { cascade_descriptors };
                
                CFDictionaryRef attributes = CFDictionaryCreate(
                    kCFAllocatorDefault,
                    (const void**)keys,
                    (const void**)values,
                    1,
                    &kCFTypeDictionaryKeyCallBacks,
                    &kCFTypeDictionaryValueCallBacks
                );
                
                if (attributes != nullptr) {
                    descriptor = CTFontDescriptorCreateCopyWithAttributes(primary_descriptor, attributes);
                    CFRelease(attributes);
                }
                
                CFRelease(primary_descriptor);
            }
        }
        
        CFRelease(cascade_descriptors);
    } else if (cascade_descriptors != nullptr) {
        // Clean up empty cascade descriptors
        CFRelease(cascade_descriptors);
    }
    
    // Create font with descriptor (includes cascade list if available)
    if (descriptor != nullptr) {
        // Use descriptor to create font with cascade list
        g_base_font = CTFontCreateWithFontDescriptor(descriptor, font_size, nullptr);
        CFRelease(descriptor);
    } else {
        // No cascade list, create font directly
        g_base_font = CTFontCreateWithName(font_name, font_size, nullptr);
    }
    
    CFRelease(font_name);  // Release the CFString we created
    
    if (g_base_font == nullptr) {
        throw std::runtime_error("Failed to create base font");
    }
    
    // Create caches
    try {
        g_color_cache = new ColorCache(256);
        g_font_cache = new FontCache(g_base_font);
        g_attr_dict_cache = new AttributeDictCache(g_font_cache, g_color_cache);
    } catch (...) {
        // Cleanup on failure
        if (g_attr_dict_cache != nullptr) {
            delete g_attr_dict_cache;
            g_attr_dict_cache = nullptr;
        }
        if (g_font_cache != nullptr) {
            delete g_font_cache;
            g_font_cache = nullptr;
        }
        if (g_color_cache != nullptr) {
            delete g_color_cache;
            g_color_cache = nullptr;
        }
        if (g_base_font != nullptr) {
            CFRelease(g_base_font);
            g_base_font = nullptr;
        }
        throw;
    }
}

//=============================================================================
// Main Rendering Function
//=============================================================================

/**
 * Main rendering function exposed to Python.
 * Renders a frame using CoreGraphics/CoreText APIs.
 * 
 * This function implements:
 * - Task 14.1: Parameter validation
 * - Task 14.2: Rendering pipeline
 * - Task 14.3: Error handling
 * 
 * @param self Module object (unused)
 * @param args Positional arguments tuple
 * @param kwargs Keyword arguments dictionary
 * @return None on success, nullptr on error (with Python exception set)
 */
static PyObject* render_frame(PyObject* self, PyObject* args, PyObject* kwargs) {
    // Start timing for performance metrics
    auto start_time = std::chrono::high_resolution_clock::now();
    
    try {
        //=====================================================================
        // Task 14.1: Parameter Validation
        //=====================================================================
        
        // Define parameter names for keyword argument parsing
        static const char* kwlist[] = {
            "context",
            "grid",
            "color_pairs",
            "dirty_rect",
            "char_width",
            "char_height",
            "rows",
            "cols",
            "offset_x",
            "offset_y",
            "cursor_visible",
            "cursor_row",
            "cursor_col",
            "marked_text",
            "selected_range_location",
            "selected_range_length",
            "font_ascent",
            "font_names",
            "font_size",
            nullptr
        };
        
        // Parameter variables
        unsigned long long context_ptr = 0;  // CGContextRef as integer
        PyObject* grid_obj = nullptr;
        PyObject* color_pairs_obj = nullptr;
        PyObject* dirty_rect_obj = nullptr;
        double char_width = 0.0;
        double char_height = 0.0;
        int rows = 0;
        int cols = 0;
        double offset_x = 0.0;
        double offset_y = 0.0;
        int cursor_visible = 0;  // Python bool as int
        int cursor_row = 0;
        int cursor_col = 0;
        const char* marked_text = nullptr;
        int selected_range_location = 0;
        int selected_range_length = 0;
        double font_ascent = 0.0;
        PyObject* font_names_obj = nullptr;  // Python list or string of font names
        double font_size = 12.0;  // Default font size
        
        // Parse arguments
        if (!PyArg_ParseTupleAndKeywords(
            args, kwargs,
            "KOOOddiiddpii|ziidOd:render_frame",
            const_cast<char**>(kwlist),
            &context_ptr,
            &grid_obj,
            &color_pairs_obj,
            &dirty_rect_obj,
            &char_width,
            &char_height,
            &rows,
            &cols,
            &offset_x,
            &offset_y,
            &cursor_visible,
            &cursor_row,
            &cursor_col,
            &marked_text,
            &selected_range_location,
            &selected_range_length,
            &font_ascent,
            &font_names_obj,
            &font_size
        )) {
            // PyArg_ParseTupleAndKeywords sets the exception
            return nullptr;
        }
        
        // Validate CGContext is not null
        if (context_ptr == 0) {
            PyErr_SetString(PyExc_ValueError, "CGContext cannot be null");
            return nullptr;
        }
        
        CGContextRef context = reinterpret_cast<CGContextRef>(context_ptr);
        
        // Validate grid dimensions
        if (rows <= 0 || cols <= 0) {
            PyErr_SetString(
                PyExc_ValueError,
                "Grid dimensions must be positive (rows > 0, cols > 0)"
            );
            return nullptr;
        }
        
        if (rows > 10000 || cols > 10000) {
            PyErr_SetString(
                PyExc_ValueError,
                "Grid dimensions too large (max 10000x10000)"
            );
            return nullptr;
        }
        
        // Validate char dimensions
        if (char_width <= 0.0 || char_height <= 0.0) {
            PyErr_SetString(
                PyExc_ValueError,
                "Character dimensions must be positive"
            );
            return nullptr;
        }
        
        // Validate grid is a list
        if (!PyList_Check(grid_obj)) {
            PyErr_SetString(PyExc_TypeError, "Grid must be a list");
            return nullptr;
        }
        
        // Validate color_pairs is a dict
        if (!PyDict_Check(color_pairs_obj)) {
            PyErr_SetString(PyExc_TypeError, "Color pairs must be a dictionary");
            return nullptr;
        }
        
        // Validate dirty_rect is a tuple with 4 elements
        if (!PyTuple_Check(dirty_rect_obj) || PyTuple_Size(dirty_rect_obj) != 4) {
            PyErr_SetString(
                PyExc_TypeError,
                "Dirty rect must be a tuple of 4 numbers (x, y, width, height)"
            );
            return nullptr;
        }
        
        // Extract dirty_rect components
        PyObject* rect_x_obj = PyTuple_GetItem(dirty_rect_obj, 0);
        PyObject* rect_y_obj = PyTuple_GetItem(dirty_rect_obj, 1);
        PyObject* rect_width_obj = PyTuple_GetItem(dirty_rect_obj, 2);
        PyObject* rect_height_obj = PyTuple_GetItem(dirty_rect_obj, 3);
        
        if (!PyFloat_Check(rect_x_obj) && !PyLong_Check(rect_x_obj)) {
            PyErr_SetString(PyExc_TypeError, "Dirty rect x must be a number");
            return nullptr;
        }
        if (!PyFloat_Check(rect_y_obj) && !PyLong_Check(rect_y_obj)) {
            PyErr_SetString(PyExc_TypeError, "Dirty rect y must be a number");
            return nullptr;
        }
        if (!PyFloat_Check(rect_width_obj) && !PyLong_Check(rect_width_obj)) {
            PyErr_SetString(PyExc_TypeError, "Dirty rect width must be a number");
            return nullptr;
        }
        if (!PyFloat_Check(rect_height_obj) && !PyLong_Check(rect_height_obj)) {
            PyErr_SetString(PyExc_TypeError, "Dirty rect height must be a number");
            return nullptr;
        }
        
        double rect_x = PyFloat_AsDouble(rect_x_obj);
        double rect_y = PyFloat_AsDouble(rect_y_obj);
        double rect_width = PyFloat_AsDouble(rect_width_obj);
        double rect_height = PyFloat_AsDouble(rect_height_obj);
        
        CGRect dirty_rect = CGRectMake(
            static_cast<CGFloat>(rect_x),
            static_cast<CGFloat>(rect_y),
            static_cast<CGFloat>(rect_width),
            static_cast<CGFloat>(rect_height)
        );
        
        //=====================================================================
        // Task 14.2: Rendering Pipeline
        //=====================================================================
        
        // Initialize caches if needed (with font parameters)
        // If font_names_obj is None, create a default list
        if (font_names_obj == nullptr || font_names_obj == Py_None) {
            // Create default font list
            font_names_obj = PyList_New(1);
            PyList_SetItem(font_names_obj, 0, PyUnicode_FromString("Menlo"));
        }
        
        initialize_caches(font_names_obj, font_size);
        
        // Parse grid and color_pairs
        std::vector<std::vector<Cell>> grid = parse_grid(grid_obj, rows, cols);
        std::unordered_map<int, ColorPair> color_pairs = parse_color_pairs(color_pairs_obj);
        
        // Calculate dirty cells
        CellRect dirty_cells = calculate_dirty_cells(
            dirty_rect,
            static_cast<CGFloat>(char_width),
            static_cast<CGFloat>(char_height),
            rows,
            cols,
            static_cast<CGFloat>(offset_x),
            static_cast<CGFloat>(offset_y)
        );
        
        // Render backgrounds
        RectangleBatcher batcher;
        render_backgrounds(
            batcher,
            grid,
            color_pairs,
            dirty_cells,
            static_cast<CGFloat>(char_width),
            static_cast<CGFloat>(char_height),
            rows,
            cols,
            static_cast<CGFloat>(offset_x),
            static_cast<CGFloat>(offset_y)
        );
        
        draw_batched_backgrounds(context, batcher, *g_color_cache);
        
        // Track batch count for metrics
        g_total_batches += batcher.size();
        
        // Render characters
        render_characters(
            context,
            grid,
            color_pairs,
            dirty_cells,
            static_cast<CGFloat>(char_width),
            static_cast<CGFloat>(char_height),
            rows,
            cols,
            static_cast<CGFloat>(offset_x),
            static_cast<CGFloat>(offset_y),
            static_cast<CGFloat>(font_ascent),
            *g_attr_dict_cache
        );
        
        // Render cursor if visible
        if (cursor_visible) {
            render_cursor(
                context,
                true,
                cursor_row,
                cursor_col,
                static_cast<CGFloat>(char_width),
                static_cast<CGFloat>(char_height),
                rows,
                static_cast<CGFloat>(offset_x),
                static_cast<CGFloat>(offset_y)
            );
        }
        
        // Render marked text if present
        if (marked_text != nullptr && marked_text[0] != '\0') {
            render_marked_text(
                context,
                marked_text,
                cursor_row,
                cursor_col,
                static_cast<CGFloat>(char_width),
                static_cast<CGFloat>(char_height),
                rows,
                static_cast<CGFloat>(offset_x),
                static_cast<CGFloat>(offset_y),
                static_cast<CGFloat>(font_ascent),
                g_base_font,
                *g_color_cache,
                selected_range_location,
                selected_range_length
            );
        }
        
        // Update performance metrics
        auto end_time = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(
            end_time - start_time
        );
        double render_time_ms = duration.count() / 1000.0;
        
        g_frames_rendered++;
        g_total_render_time_ms += render_time_ms;
        
        // Performance logging (if enabled)
        if (g_enable_perf_logging && g_frames_rendered % 60 == 0) {
            // Log every 60 frames (approximately once per second at 60fps)
            // Calculate averages over the last 60 frames
            double avg_render_time = g_total_render_time_ms / 60.0;
            double avg_batches = g_total_batches / 60.0;
            double avg_chars = g_total_characters / 60.0;
            double avg_splits = g_total_batch_splits / 60.0;
            double font_hit_rate = g_font_lookups > 0 ? 
                (g_font_cache_hits * 100.0 / g_font_lookups) : 0.0;
            
            // Log performance metrics
            fprintf(stderr, 
                "[C++ Renderer] Frame %zu: %.2fms | Batches: %.1f | Chars: %.1f | "
                "Splits: %.1f | Font hits: %.1f%%",
                g_frames_rendered, avg_render_time, avg_batches, avg_chars, 
                avg_splits, font_hit_rate
            );
            
            // Include last failed character if any lookups failed
            if (g_last_failed_char != 0) {
                fprintf(stderr, " | Last fail: U+%04X", static_cast<unsigned int>(g_last_failed_char));
            }
            
            fprintf(stderr, "\n");
            
            // Reset cumulative metrics for next logging period
            // This ensures each log shows averages for the last 60 frames only
            g_total_render_time_ms = 0.0;
            g_total_batches = 0;
            g_total_characters = 0;
            g_total_batch_splits = 0;
            g_font_lookups = 0;
            g_font_cache_hits = 0;
            g_last_failed_char = 0;  // Reset failed character tracking
        }
        
        // Success - return None
        Py_RETURN_NONE;
        
    } catch (const std::bad_alloc& e) {
        //=====================================================================
        // Task 14.3: Error Handling - Memory allocation errors
        //=====================================================================
        PyErr_SetString(PyExc_MemoryError, "Memory allocation failed during rendering");
        return nullptr;
        
    } catch (const std::runtime_error& e) {
        //=====================================================================
        // Task 14.3: Error Handling - Runtime errors
        //=====================================================================
        // Log error for debugging
        fprintf(stderr, "C++ renderer error: %s\n", e.what());
        
        // Convert C++ exception to Python exception
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
        
    } catch (const std::exception& e) {
        //=====================================================================
        // Task 14.3: Error Handling - Other standard exceptions
        //=====================================================================
        // Log error for debugging
        fprintf(stderr, "C++ renderer exception: %s\n", e.what());
        
        // Convert C++ exception to Python exception
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
        
    } catch (...) {
        //=====================================================================
        // Task 14.3: Error Handling - Unknown exceptions
        //=====================================================================
        // Log error for debugging
        fprintf(stderr, "C++ renderer: Unknown exception occurred\n");
        
        // Convert to Python exception
        PyErr_SetString(PyExc_RuntimeError, "Unknown error occurred in C++ renderer");
        return nullptr;
    }
}

/**
 * Clear all internal caches.
 * Releases cached fonts, colors, and attribute dictionaries.
 * 
 * @param self Module object (unused)
 * @param args Arguments (unused)
 * @return None
 */
static PyObject* clear_caches(PyObject* self, PyObject* args) {
    try {
        if (g_attr_dict_cache != nullptr) {
            g_attr_dict_cache->clear();
        }
        if (g_font_cache != nullptr) {
            g_font_cache->clear();
        }
        if (g_color_cache != nullptr) {
            g_color_cache->clear();
        }
        
        Py_RETURN_NONE;
        
    } catch (const std::exception& e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    }
}

/**
 * Get performance metrics as a Python dictionary.
 * Returns metrics about rendering performance and cache effectiveness.
 * 
 * @param self Module object (unused)
 * @param args Arguments (unused)
 * @return Dictionary containing performance metrics
 */
static PyObject* get_performance_metrics(PyObject* self, PyObject* args) {
    try {
        PyObject* metrics = PyDict_New();
        if (metrics == nullptr) {
            return nullptr;
        }
        
        // Calculate averages
        double avg_render_time_ms = 0.0;
        double avg_batches_per_frame = 0.0;
        
        if (g_frames_rendered > 0) {
            avg_render_time_ms = g_total_render_time_ms / g_frames_rendered;
            avg_batches_per_frame = static_cast<double>(g_total_batches) / g_frames_rendered;
        }
        
        // Get cache metrics
        size_t attr_dict_hits = 0;
        size_t attr_dict_misses = 0;
        double cache_hit_rate = 0.0;
        
        if (g_attr_dict_cache != nullptr) {
            attr_dict_hits = g_attr_dict_cache->get_hit_count();
            attr_dict_misses = g_attr_dict_cache->get_miss_count();
            
            size_t total_accesses = attr_dict_hits + attr_dict_misses;
            if (total_accesses > 0) {
                cache_hit_rate = (static_cast<double>(attr_dict_hits) / total_accesses) * 100.0;
            }
        }
        
        // Add metrics to dictionary
        PyDict_SetItemString(metrics, "frames_rendered", 
                            PyLong_FromSize_t(g_frames_rendered));
        PyDict_SetItemString(metrics, "total_render_time_ms", 
                            PyFloat_FromDouble(g_total_render_time_ms));
        PyDict_SetItemString(metrics, "avg_render_time_ms", 
                            PyFloat_FromDouble(avg_render_time_ms));
        PyDict_SetItemString(metrics, "total_batches", 
                            PyLong_FromSize_t(g_total_batches));
        PyDict_SetItemString(metrics, "avg_batches_per_frame", 
                            PyFloat_FromDouble(avg_batches_per_frame));
        
        // Add new batching metrics
        double avg_chars_per_frame = g_frames_rendered > 0 ? 
            static_cast<double>(g_total_characters) / g_frames_rendered : 0.0;
        double avg_splits_per_frame = g_frames_rendered > 0 ?
            static_cast<double>(g_total_batch_splits) / g_frames_rendered : 0.0;
        double avg_chars_per_batch = g_total_batches > 0 ?
            static_cast<double>(g_total_characters) / g_total_batches : 0.0;
        
        PyDict_SetItemString(metrics, "total_characters",
                            PyLong_FromSize_t(g_total_characters));
        PyDict_SetItemString(metrics, "avg_chars_per_frame",
                            PyFloat_FromDouble(avg_chars_per_frame));
        PyDict_SetItemString(metrics, "avg_chars_per_batch",
                            PyFloat_FromDouble(avg_chars_per_batch));
        PyDict_SetItemString(metrics, "total_batch_splits",
                            PyLong_FromSize_t(g_total_batch_splits));
        PyDict_SetItemString(metrics, "avg_splits_per_frame",
                            PyFloat_FromDouble(avg_splits_per_frame));
        
        // Add font lookup metrics
        double font_hit_rate = g_font_lookups > 0 ?
            (static_cast<double>(g_font_cache_hits) / g_font_lookups) * 100.0 : 0.0;
        
        PyDict_SetItemString(metrics, "font_lookups",
                            PyLong_FromSize_t(g_font_lookups));
        PyDict_SetItemString(metrics, "font_cache_hits",
                            PyLong_FromSize_t(g_font_cache_hits));
        PyDict_SetItemString(metrics, "font_hit_rate_percent",
                            PyFloat_FromDouble(font_hit_rate));
        
        // Add attribute dictionary cache metrics
        PyDict_SetItemString(metrics, "attr_dict_cache_hits", 
                            PyLong_FromSize_t(attr_dict_hits));
        PyDict_SetItemString(metrics, "attr_dict_cache_misses", 
                            PyLong_FromSize_t(attr_dict_misses));
        PyDict_SetItemString(metrics, "attr_dict_cache_hit_rate", 
                            PyFloat_FromDouble(cache_hit_rate));
        
        return metrics;
        
    } catch (const std::exception& e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    }
}

/**
 * Reset performance metrics counters to zero.
 * Also resets cache metrics.
 * 
 * @param self Module object (unused)
 * @param args Arguments (unused)
 * @return None
 */
static PyObject* reset_metrics(PyObject* self, PyObject* args) {
    try {
        // Reset global metrics
        g_frames_rendered = 0;
        g_total_render_time_ms = 0.0;
        g_total_batches = 0;
        g_total_characters = 0;
        g_total_batch_splits = 0;
        g_font_lookups = 0;
        g_font_cache_hits = 0;
        g_last_failed_char = 0;
        
        // Reset cache metrics
        if (g_attr_dict_cache != nullptr) {
            g_attr_dict_cache->reset_metrics();
        }
        
        Py_RETURN_NONE;
        
    } catch (const std::exception& e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    }
}

/**
 * Enable or disable performance logging.
 * When enabled, logs performance metrics to stderr every 60 frames.
 * 
 * @param self Module object (unused)
 * @param args Arguments tuple containing a boolean (enable/disable)
 * @return None
 */
static PyObject* enable_perf_logging(PyObject* self, PyObject* args) {
    int enable = 0;
    
    if (!PyArg_ParseTuple(args, "p", &enable)) {
        return nullptr;
    }
    
    g_enable_perf_logging = (enable != 0);
    
    if (g_enable_perf_logging) {
        fprintf(stderr, "[C++ Renderer] Performance logging enabled\n");
    } else {
        fprintf(stderr, "[C++ Renderer] Performance logging disabled\n");
    }
    
    Py_RETURN_NONE;
}

//=============================================================================
// Drag-and-Drop Support
//=============================================================================

/**
 * Start a native macOS drag-and-drop session.
 * 
 * This function initiates a drag operation using macOS NSDraggingSession.
 * It creates NSDraggingItem objects for each file URL, sets up the pasteboard,
 * generates a drag image with text overlay, and begins the drag session.
 * 
 * The drag session is managed by macOS, which handles:
 * - Drag cursor and visual feedback
 * - Drop target validation
 * - File operation type (copy/move/link) based on modifiers
 * - Completion/cancellation notifications
 * 
 * @param self Module object (unused)
 * @param args Arguments tuple containing:
 *             - view: NSView object (as Python integer/long)
 *             - file_urls: List of file:// URL strings
 *             - drag_image_text: Text to display in drag image (str)
 *             - event: NSEvent object (as Python integer/long, optional, default 0)
 * @return PyObject* True if drag started successfully, False otherwise
 */
static PyObject* start_drag_session(PyObject* self, PyObject* args) {
    // Parse arguments
    PyObject* view_obj = nullptr;
    PyObject* file_urls_obj = nullptr;
    const char* drag_image_text = nullptr;
    PyObject* event_obj = nullptr;
    
    if (!PyArg_ParseTuple(args, "OOsO", &view_obj, &file_urls_obj, &drag_image_text, &event_obj)) {
        PyErr_SetString(PyExc_TypeError, "Expected (view, file_urls, drag_image_text, event)");
        return nullptr;
    }
    
    // Validate file_urls is a list
    if (!PyList_Check(file_urls_obj)) {
        PyErr_SetString(PyExc_TypeError, "file_urls must be a list");
        return nullptr;
    }
    
    Py_ssize_t url_count = PyList_Size(file_urls_obj);
    if (url_count == 0) {
        PyErr_SetString(PyExc_ValueError, "file_urls list cannot be empty");
        return nullptr;
    }
    
    // Extract NSView pointer from Python object
    // The view is passed as a Python integer containing the pointer address
    void* view_ptr = PyLong_AsVoidPtr(view_obj);
    if (view_ptr == nullptr && PyErr_Occurred()) {
        PyErr_SetString(PyExc_TypeError, "Invalid view object");
        return nullptr;
    }
    
    // Extract NSEvent pointer from Python object (may be 0/nullptr if not provided)
    void* event_ptr = PyLong_AsVoidPtr(event_obj);
    // Clear any error from PyLong_AsVoidPtr if event_obj was 0
    if (event_ptr == nullptr) {
        PyErr_Clear();
    }
    
    // Cast to NSView (using id to avoid Objective-C++ requirement)
    id view = (id)view_ptr;
    
    // Create NSMutableArray for file URLs
    id file_url_array = ((id(*)(id, SEL))objc_msgSend)((id)objc_getClass("NSMutableArray"), sel_registerName("array"));
    
    // Convert Python file:// URL strings to NSURLs
    for (Py_ssize_t i = 0; i < url_count; ++i) {
        PyObject* url_str_obj = PyList_GetItem(file_urls_obj, i);  // Borrowed reference
        
        if (!PyUnicode_Check(url_str_obj)) {
            PyErr_SetString(PyExc_TypeError, "All file URLs must be strings");
            return nullptr;
        }
        
        // Get UTF-8 string from Python Unicode object
        const char* url_str = PyUnicode_AsUTF8(url_str_obj);
        if (url_str == nullptr) {
            return nullptr;  // PyUnicode_AsUTF8 sets exception
        }
        
        // Create NSString from UTF-8
        id ns_url_string = ((id(*)(id, SEL, const char*))objc_msgSend)(
            (id)objc_getClass("NSString"),
            sel_registerName("stringWithUTF8String:"),
            url_str
        );
        
        if (ns_url_string == nullptr) {
            PyErr_SetString(PyExc_RuntimeError, "Failed to create NSString from URL");
            return nullptr;
        }
        
        // Create NSURL from string
        id ns_url = ((id(*)(id, SEL, id))objc_msgSend)(
            (id)objc_getClass("NSURL"),
            sel_registerName("URLWithString:"),
            ns_url_string
        );
        
        if (ns_url == nullptr) {
            PyErr_Format(PyExc_ValueError, "Invalid file URL: %s", url_str);
            return nullptr;
        }
        
        // Add to array
        ((void(*)(id, SEL, id))objc_msgSend)(file_url_array, sel_registerName("addObject:"), ns_url);
    }
    
    // Create NSString for drag image text
    id drag_text_string = ((id(*)(id, SEL, const char*))objc_msgSend)(
        (id)objc_getClass("NSString"),
        sel_registerName("stringWithUTF8String:"),
        drag_image_text
    );
    
    if (drag_text_string == nullptr) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to create NSString for drag image text");
        return nullptr;
    }
    
    // Create drag image with text overlay
    // Create NSImage with text
    id font = ((id(*)(id, SEL, CGFloat))objc_msgSend)(
        (id)objc_getClass("NSFont"),
        sel_registerName("systemFontOfSize:"),
        14.0
    );
    
    // Create attributes dictionary for text
    id attributes_dict = ((id(*)(id, SEL))objc_msgSend)((id)objc_getClass("NSMutableDictionary"), sel_registerName("dictionary"));
    
    // Get NSFontAttributeName constant
    // This is a global NSString constant, we need to create an NSString with the same value
    id font_attr_key = ((id(*)(id, SEL, const char*))objc_msgSend)(
        (id)objc_getClass("NSString"),
        sel_registerName("stringWithUTF8String:"),
        "NSFont"
    );
    
    ((void(*)(id, SEL, id, id))objc_msgSend)(
        attributes_dict,
        sel_registerName("setObject:forKey:"),
        font,
        font_attr_key
    );
    
    // Calculate text size
    CGSize text_size = ((CGSize(*)(id, SEL, id))objc_msgSend)(
        drag_text_string,
        sel_registerName("sizeWithAttributes:"),
        attributes_dict
    );
    
    // Add padding to image size
    CGFloat padding = 10.0;
    CGSize image_size = CGSizeMake(
        text_size.width + padding * 2,
        text_size.height + padding * 2
    );
    
    // Create NSImage
    id drag_image = ((id(*)(id, SEL, CGSize))objc_msgSend)(
        ((id(*)(id, SEL))objc_msgSend)((id)objc_getClass("NSImage"), sel_registerName("alloc")),
        sel_registerName("initWithSize:"),
        image_size
    );
    
    if (drag_image == nullptr) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to create drag image");
        return nullptr;
    }
    
    // Lock focus and draw
    ((void(*)(id, SEL))objc_msgSend)(drag_image, sel_registerName("lockFocus"));
    
    // Draw semi-transparent background
    id background_color = ((id(*)(id, SEL, CGFloat, CGFloat))objc_msgSend)(
        (id)objc_getClass("NSColor"),
        sel_registerName("colorWithWhite:alpha:"),
        0.9,
        0.8
    );
    ((void(*)(id, SEL))objc_msgSend)(background_color, sel_registerName("set"));
    
    CGRect background_rect = CGRectMake(0, 0, image_size.width, image_size.height);
    ((void(*)(id, SEL, CGRect))objc_msgSend)(
        (id)objc_getClass("NSBezierPath"),
        sel_registerName("fillRect:"),
        background_rect
    );
    
    // Draw text
    CGPoint text_point = CGPointMake(padding, padding);
    ((void(*)(id, SEL, CGPoint, id))objc_msgSend)(
        drag_text_string,
        sel_registerName("drawAtPoint:withAttributes:"),
        text_point,
        attributes_dict
    );
    
    ((void(*)(id, SEL))objc_msgSend)(drag_image, sel_registerName("unlockFocus"));
    
    // Create NSDraggingItem array - one item per URL
    id dragging_items_array = ((id(*)(id, SEL))objc_msgSend)((id)objc_getClass("NSMutableArray"), sel_registerName("array"));
    
    // Get mouse location for positioning drag image
    id window = ((id(*)(id, SEL))objc_msgSend)(view, sel_registerName("window"));
    CGPoint mouse_location_window = ((CGPoint(*)(id, SEL))objc_msgSend)(window, sel_registerName("mouseLocationOutsideOfEventStream"));
    CGPoint mouse_location = ((CGPoint(*)(id, SEL, CGPoint, id))objc_msgSend)(
        view,
        sel_registerName("convertPoint:fromView:"),
        mouse_location_window,
        nullptr
    );
    
    // Create dragging frame for the image
    CGRect dragging_frame = CGRectMake(
        mouse_location.x - image_size.width / 2,
        mouse_location.y - image_size.height / 2,
        image_size.width,
        image_size.height
    );
    
    // Create a dragging item for each URL
    for (Py_ssize_t i = 0; i < url_count; ++i) {
        id ns_url = ((id(*)(id, SEL, unsigned long))objc_msgSend)(file_url_array, sel_registerName("objectAtIndex:"), (unsigned long)i);
        
        // Create NSDraggingItem with this URL as the pasteboard writer
        id dragging_item = ((id(*)(id, SEL, id))objc_msgSend)(
            ((id(*)(id, SEL))objc_msgSend)((id)objc_getClass("NSDraggingItem"), sel_registerName("alloc")),
            sel_registerName("initWithPasteboardWriter:"),
            ns_url
        );
        
        if (dragging_item == nullptr) {
            PyErr_SetString(PyExc_RuntimeError, "Failed to create NSDraggingItem");
            return nullptr;
        }
        
        // Set dragging frame and image (only for first item to avoid overlapping images)
        if (i == 0) {
            ((void(*)(id, SEL, CGRect, id))objc_msgSend)(
                dragging_item,
                sel_registerName("setDraggingFrame:contents:"),
                dragging_frame,
                drag_image
            );
        } else {
            // For additional items, use same frame but no image
            ((void(*)(id, SEL, CGRect, id))objc_msgSend)(
                dragging_item,
                sel_registerName("setDraggingFrame:contents:"),
                dragging_frame,
                nullptr
            );
        }
        
        // Add to array
        ((void(*)(id, SEL, id))objc_msgSend)(dragging_items_array, sel_registerName("addObject:"), dragging_item);
    }
    
    // Get current event for drag session
    // Use provided event if available, otherwise try to get current event from NSApp
    id current_event = nullptr;
    if (event_ptr != nullptr) {
        current_event = (id)event_ptr;
    } else {
        current_event = ((id(*)(id, SEL))objc_msgSend)(
            ((id(*)(id, SEL))objc_msgSend)((id)objc_getClass("NSApp"), sel_registerName("sharedApplication")),
            sel_registerName("currentEvent")
        );
    }
    
    if (current_event == nullptr) {
        PyErr_SetString(PyExc_RuntimeError, "No current event available for drag session");
        return nullptr;
    }
    
    // Begin dragging session
    // NSDraggingSession* session = [view beginDraggingSessionWithItems:draggingItems event:currentEvent source:view];
    id dragging_session = ((id(*)(id, SEL, id, id, id))objc_msgSend)(
        view,
        sel_registerName("beginDraggingSessionWithItems:event:source:"),
        dragging_items_array,
        current_event,
        view
    );
    
    if (dragging_session == nullptr) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to begin dragging session");
        return nullptr;
    }
    
    // Set dragging formation to default (files stack)
    ((void(*)(id, SEL, long))objc_msgSend)(
        dragging_session,
        sel_registerName("setDraggingFormation:"),
        0  // NSDraggingFormationDefault
    );
    
    // Enable animation back to start position on cancel/fail
    ((void(*)(id, SEL, unsigned long))objc_msgSend)(
        dragging_session,
        sel_registerName("setAnimatesToStartingPositionsOnCancelOrFail:"),
        1  // YES - animate back on cancel
    );
    
    // Note: The drag operation mask (Copy | Move) is set by the NSDraggingSource
    // protocol method draggingSession:sourceOperationMaskForDraggingContext:
    // implemented in TTKView in coregraphics_backend.py
    
    // Success
    Py_RETURN_TRUE;
}
