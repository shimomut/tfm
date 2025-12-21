// cpp_renderer.cpp - C++ rendering backend for CoreGraphics
// Provides direct CoreGraphics/CoreText API access for improved performance

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <CoreGraphics/CoreGraphics.h>
#include <CoreText/CoreText.h>
#include <CoreFoundation/CoreFoundation.h>

#include <string>
#include <vector>
#include <unordered_map>
#include <optional>
#include <cstdint>
#include <cmath>
#include <chrono>

// Module version
#define CPP_RENDERER_VERSION "1.0.0"

//=============================================================================
// Data Structures
//=============================================================================

// Cell structure representing a single grid cell
struct Cell {
    std::string character;  // UTF-8 encoded character
    int color_pair;         // Color pair ID
    int attributes;         // Text attributes (BOLD, UNDERLINE, etc.)
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
    {nullptr, nullptr, 0, nullptr}  // Sentinel
};

//=============================================================================
// Module Definition
//=============================================================================

static struct PyModuleDef cpp_renderer_module = {
    PyModuleDef_HEAD_INIT,
    "cpp_renderer",                                      // Module name
    "C++ rendering backend for CoreGraphics/CoreText",  // Module docstring
    -1,                                                  // Module state size
    CppRendererMethods                                   // Module methods
};

//=============================================================================
// Module Initialization
//=============================================================================

PyMODINIT_FUNC PyInit_cpp_renderer(void) {
    PyObject* module = PyModule_Create(&cpp_renderer_module);
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
            
            // Validate tuple has 3 elements
            if (PyTuple_Size(cell_obj) != 3) {
                throw std::runtime_error(
                    "Grid cell (" + std::to_string(row) + ", " + std::to_string(col) +
                    ") must have 3 elements (char, color_pair, attributes)"
                );
            }
            
            // Extract character (UTF-8 string)
            PyObject* char_obj = PyTuple_GetItem(cell_obj, 0);  // Borrowed reference
            if (!PyUnicode_Check(char_obj)) {
                throw std::runtime_error(
                    "Grid cell (" + std::to_string(row) + ", " + std::to_string(col) +
                    ") character must be a string"
                );
            }
            
            // Convert Python string to UTF-8 C++ string
            const char* char_utf8 = PyUnicode_AsUTF8(char_obj);
            if (char_utf8 == nullptr) {
                throw std::runtime_error(
                    "Failed to convert character to UTF-8 at (" + std::to_string(row) +
                    ", " + std::to_string(col) + ")"
                );
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
            
            // Create cell and add to row
            Cell cell;
            cell.character = char_utf8;
            cell.color_pair = static_cast<int>(color_pair);
            cell.attributes = static_cast<int>(attributes);
            
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
                CGFloat cell_width = char_width;
                CGFloat cell_height = char_height;
                
                // Extend left edge (leftmost column)
                if (col == left_col) {
                    cell_x = 0;
                    cell_width = char_width + offset_x;
                }
                
                // Extend right edge (rightmost column)
                if (col == right_col) {
                    cell_width = char_width + offset_x;
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
                batcher.add_cell(x, y, char_width, char_height, bg_rgb);
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
    std::string text;        // Accumulated UTF-8 text
    int font_attributes;     // Font attributes (BOLD, etc.)
    uint32_t fg_rgb;         // Foreground color (packed RGB)
    bool underline;          // Underline flag
    CGFloat x;               // Starting x position
    CGFloat y;               // Starting y position
};

/**
 * Check if a character is a wide character (occupies 2 grid cells).
 * Wide characters include CJK characters and other full-width Unicode characters.
 * 
 * @param utf8_char UTF-8 encoded character string
 * @return true if the character is wide, false otherwise
 */
static bool is_wide_character(const std::string& utf8_char) {
    // Empty string is not wide
    if (utf8_char.empty()) {
        return false;
    }
    
    // Decode UTF-8 to get Unicode code point
    const unsigned char* bytes = reinterpret_cast<const unsigned char*>(utf8_char.c_str());
    uint32_t codepoint = 0;
    
    // UTF-8 decoding
    if ((bytes[0] & 0x80) == 0) {
        // 1-byte character (ASCII)
        codepoint = bytes[0];
    } else if ((bytes[0] & 0xE0) == 0xC0) {
        // 2-byte character
        if (utf8_char.length() < 2) return false;
        codepoint = ((bytes[0] & 0x1F) << 6) | (bytes[1] & 0x3F);
    } else if ((bytes[0] & 0xF0) == 0xE0) {
        // 3-byte character
        if (utf8_char.length() < 3) return false;
        codepoint = ((bytes[0] & 0x0F) << 12) | ((bytes[1] & 0x3F) << 6) | (bytes[2] & 0x3F);
    } else if ((bytes[0] & 0xF8) == 0xF0) {
        // 4-byte character
        if (utf8_char.length() < 4) return false;
        codepoint = ((bytes[0] & 0x07) << 18) | ((bytes[1] & 0x3F) << 12) |
                    ((bytes[2] & 0x3F) << 6) | (bytes[3] & 0x3F);
    } else {
        return false;
    }
    
    // Check if codepoint is in wide character ranges
    // CJK Unified Ideographs: U+4E00 - U+9FFF
    // CJK Compatibility Ideographs: U+F900 - U+FAFF
    // Hangul Syllables: U+AC00 - U+D7AF
    // Hiragana: U+3040 - U+309F
    // Katakana: U+30A0 - U+30FF
    // Fullwidth ASCII variants: U+FF00 - U+FFEF
    
    if ((codepoint >= 0x4E00 && codepoint <= 0x9FFF) ||   // CJK Unified Ideographs
        (codepoint >= 0xF900 && codepoint <= 0xFAFF) ||   // CJK Compatibility
        (codepoint >= 0xAC00 && codepoint <= 0xD7AF) ||   // Hangul
        (codepoint >= 0x3040 && codepoint <= 0x309F) ||   // Hiragana
        (codepoint >= 0x30A0 && codepoint <= 0x30FF) ||   // Katakana
        (codepoint >= 0xFF00 && codepoint <= 0xFFEF)) {   // Fullwidth ASCII
        return true;
    }
    
    return false;
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
    AttributeDictCache& attr_dict_cache
);

// Forward declaration for draw_character_batch
static void draw_character_batch(
    CGContextRef context,
    const CharacterBatch& batch,
    AttributeDictCache& attr_dict_cache
);

/**
 * Draw a batch of characters with the same attributes.
 * Creates a CFAttributedString with the text and attributes, then uses
 * CTLineDraw to render the text to the CoreGraphics context.
 * 
 * @param context CGContextRef to draw to
 * @param batch CharacterBatch containing the text and attributes to draw
 * @param attr_dict_cache AttributeDictCache for getting attribute dictionaries
 */
static void draw_character_batch(
    CGContextRef context,
    const CharacterBatch& batch,
    AttributeDictCache& attr_dict_cache
) {
    // Get attribute dictionary from cache
    CFDictionaryRef attributes = attr_dict_cache.get_attributes(
        batch.font_attributes,
        batch.fg_rgb,
        batch.underline
    );
    
    if (attributes == nullptr) {
        // Failed to get attributes - skip this batch
        return;
    }
    
    // Create CFString from UTF-8 text
    CFStringRef text_string = CFStringCreateWithCString(
        kCFAllocatorDefault,
        batch.text.c_str(),
        kCFStringEncodingUTF8
    );
    
    if (text_string == nullptr) {
        // Failed to create CFString - skip this batch
        return;
    }
    
    // Create CFAttributedString with text and attributes
    CFAttributedStringRef attributed_string = CFAttributedStringCreate(
        kCFAllocatorDefault,
        text_string,
        attributes
    );
    
    // Release text_string (no longer needed)
    CFRelease(text_string);
    
    if (attributed_string == nullptr) {
        // Failed to create attributed string - skip this batch
        return;
    }
    
    // Create CTLine from attributed string
    CTLineRef line = CTLineCreateWithAttributedString(attributed_string);
    
    // Release attributed_string (no longer needed)
    CFRelease(attributed_string);
    
    if (line == nullptr) {
        // Failed to create CTLine - skip this batch
        return;
    }
    
    // Set text position in the graphics context
    // CoreText draws text with the baseline at the specified y position
    // We need to adjust y to account for font descent to position text correctly
    // For now, we'll use the y position directly and rely on the font metrics
    // being consistent with the grid layout
    CGContextSetTextPosition(context, batch.x, batch.y);
    
    // Draw the line
    CTLineDraw(line, context);
    
    // Release CTLine
    CFRelease(line);
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
    AttributeDictCache& attr_dict_cache
) {
    // Current batch being accumulated
    std::optional<CharacterBatch> current_batch;
    
    // Iterate through dirty region cells
    for (int row = dirty_cells.start_row; row < dirty_cells.end_row; ++row) {
        for (int col = dirty_cells.start_col; col < dirty_cells.end_col; ++col) {
            // Get cell from grid
            const Cell& cell = grid[row][col];
            
            // Skip spaces - backgrounds already rendered
            if (cell.character == " " || cell.character.empty()) {
                // Finish current batch if any
                if (current_batch.has_value()) {
                    draw_character_batch(context, current_batch.value(), attr_dict_cache);
                    current_batch = std::nullopt;
                }
                continue;
            }
            
            // Check if this is a placeholder cell for a wide character
            // Placeholder cells have empty strings and should be skipped
            if (cell.character.empty()) {
                // Finish current batch if any
                if (current_batch.has_value()) {
                    draw_character_batch(context, current_batch.value(), attr_dict_cache);
                    current_batch = std::nullopt;
                }
                continue;
            }
            
            // Get color pair for this cell
            auto color_it = color_pairs.find(cell.color_pair);
            if (color_it == color_pairs.end()) {
                // Color pair not found - skip this cell
                if (current_batch.has_value()) {
                    draw_character_batch(context, current_batch.value(), attr_dict_cache);
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
            
            // Check if we can extend the current batch
            bool can_extend = false;
            if (current_batch.has_value()) {
                CharacterBatch& batch = current_batch.value();
                
                // Can extend if:
                // 1. Same row (y coordinate matches)
                // 2. Same attributes (font, color, underline)
                // 3. Adjacent position (x is at the right edge of current batch)
                bool same_row = (std::abs(batch.y - y) < 0.01f);
                bool same_attributes = (batch.font_attributes == font_attributes &&
                                       batch.fg_rgb == fg_rgb &&
                                       batch.underline == underline);
                
                // Calculate expected x position for next character
                // Need to account for wide characters in the batch
                CGFloat expected_x = batch.x;
                for (size_t i = 0; i < batch.text.length(); ) {
                    // Find the next UTF-8 character boundary
                    size_t char_start = i;
                    while (i < batch.text.length() && (batch.text[i] & 0xC0) == 0x80) {
                        ++i;
                    }
                    if (i < batch.text.length()) {
                        ++i;
                    }
                    
                    // Extract the character
                    std::string batch_char = batch.text.substr(char_start, i - char_start);
                    
                    // Add width (double for wide characters)
                    if (is_wide_character(batch_char)) {
                        expected_x += char_width * 2.0f;
                    } else {
                        expected_x += char_width;
                    }
                }
                
                bool adjacent = (std::abs(expected_x - x) < 0.01f);
                
                can_extend = same_row && same_attributes && adjacent;
            }
            
            if (can_extend) {
                // Extend current batch
                current_batch.value().text += cell.character;
            } else {
                // Finish current batch if any
                if (current_batch.has_value()) {
                    draw_character_batch(context, current_batch.value(), attr_dict_cache);
                }
                
                // Start new batch
                CharacterBatch new_batch;
                new_batch.text = cell.character;
                new_batch.font_attributes = font_attributes;
                new_batch.fg_rgb = fg_rgb;
                new_batch.underline = underline;
                new_batch.x = x;
                new_batch.y = y;
                
                current_batch = new_batch;
            }
            
            // If this is a wide character, skip the next column (placeholder cell)
            if (is_wide_character(cell.character)) {
                // The next column should be a placeholder, so we'll skip it
                // in the next iteration
            }
        }
        
        // Finish batch at end of row
        if (current_batch.has_value()) {
            draw_character_batch(context, current_batch.value(), attr_dict_cache);
            current_batch = std::nullopt;
        }
    }
    
    // Finish any remaining batch
    if (current_batch.has_value()) {
        draw_character_batch(context, current_batch.value(), attr_dict_cache);
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
 * Draws the marked text with an underline to indicate it's being composed.
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
 * @param base_font Base CTFontRef to use for rendering
 * @param color_cache ColorCache for getting foreground color
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
    CTFontRef base_font,
    ColorCache& color_cache
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
    
    // Create CFString from UTF-8 marked text
    CFStringRef text_string = CFStringCreateWithCString(
        kCFAllocatorDefault,
        marked_text,
        kCFStringEncodingUTF8
    );
    
    if (text_string == nullptr) {
        // Failed to create CFString - cannot render
        return;
    }
    
    // Get white color for marked text (standard IME appearance)
    CGColorRef text_color = color_cache.get_color(255, 255, 255, 1.0f);
    
    if (text_color == nullptr) {
        CFRelease(text_string);
        return;
    }
    
    // Create attribute dictionary with underline
    CFStringRef keys[3];
    CFTypeRef values[3];
    
    // Add font attribute
    keys[0] = kCTFontAttributeName;
    values[0] = base_font;
    
    // Add foreground color attribute
    keys[1] = kCTForegroundColorAttributeName;
    values[1] = text_color;
    
    // Add underline attribute (single underline)
    keys[2] = kCTUnderlineStyleAttributeName;
    int underline_style = kCTUnderlineStyleSingle;
    CFNumberRef underline_number = CFNumberCreate(
        kCFAllocatorDefault,
        kCFNumberIntType,
        &underline_style
    );
    
    if (underline_number == nullptr) {
        CFRelease(text_string);
        return;
    }
    
    values[2] = underline_number;
    
    // Create attribute dictionary
    CFDictionaryRef attributes = CFDictionaryCreate(
        kCFAllocatorDefault,
        (const void**)keys,
        (const void**)values,
        3,
        &kCFTypeDictionaryKeyCallBacks,
        &kCFTypeDictionaryValueCallBacks
    );
    
    // Release underline number (dictionary retains it)
    CFRelease(underline_number);
    
    if (attributes == nullptr) {
        CFRelease(text_string);
        return;
    }
    
    // Create CFAttributedString with text and attributes
    CFAttributedStringRef attributed_string = CFAttributedStringCreate(
        kCFAllocatorDefault,
        text_string,
        attributes
    );
    
    // Release text_string and attributes (no longer needed)
    CFRelease(text_string);
    CFRelease(attributes);
    
    if (attributed_string == nullptr) {
        return;
    }
    
    // Create CTLine from attributed string
    CTLineRef line = CTLineCreateWithAttributedString(attributed_string);
    
    // Release attributed_string (no longer needed)
    CFRelease(attributed_string);
    
    if (line == nullptr) {
        return;
    }
    
    // Set text position in the graphics context
    CGContextSetTextPosition(context, x, y);
    
    // Draw with CTLineDraw
    CTLineDraw(line, context);
    
    // Release CTLine
    CFRelease(line);
}

//=============================================================================
// Global State for Caches
//=============================================================================

// Global caches (initialized on first use)
static ColorCache* g_color_cache = nullptr;
static FontCache* g_font_cache = nullptr;
static AttributeDictCache* g_attr_dict_cache = nullptr;
static CTFontRef g_base_font = nullptr;

// Performance metrics
static size_t g_frames_rendered = 0;
static double g_total_render_time_ms = 0.0;
static size_t g_total_batches = 0;

/**
 * Initialize global caches if not already initialized.
 * Creates the base font and all cache objects.
 * 
 * @throws std::runtime_error if initialization fails
 */
static void initialize_caches() {
    if (g_color_cache != nullptr) {
        // Already initialized
        return;
    }
    
    // Create base font (Menlo 12pt - matches Python default)
    // Note: This should match the font used in CoreGraphicsBackend.__init__()
    // Python default: font_name="Menlo", font_size=12
    CFStringRef font_name = CFSTR("Menlo");
    CGFloat font_size = 12.0;
    
    g_base_font = CTFontCreateWithName(font_name, font_size, nullptr);
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
        
        // Parse arguments
        if (!PyArg_ParseTupleAndKeywords(
            args, kwargs,
            "KOOOddiiddpii|z:render_frame",
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
            &marked_text
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
        
        // Initialize caches if needed
        initialize_caches();
        
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
                g_base_font,
                *g_color_cache
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
