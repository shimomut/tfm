# Rendering Code Comparison: Core Graphics vs Metal

## Side-by-Side Implementation Comparison

This document shows actual code comparisons to illustrate the complexity difference between Core Graphics and Metal for character-grid rendering.

## 1. Drawing a Single Character

### Core Graphics: Simple ✅

```python
def draw_character(self, ctx, row, col, char, fg_color, bg_color):
    """Draw one character - 10 lines of code"""
    x = col * self.char_width
    y = row * self.char_height
    
    # Draw background
    CGContextSetRGBFillColor(ctx, *bg_color, 1.0)
    CGContextFillRect(ctx, CGRectMake(x, y, self.char_width, self.char_height))
    
    # Draw character
    attr_string = NSAttributedString.alloc().initWithString_attributes_(
        char, {NSFontAttributeName: self.font, NSForegroundColorAttributeName: fg_color}
    )
    attr_string.drawAtPoint_(NSMakePoint(x, y))
```

**Total: 10 lines**

### Metal: Complex ❌

```python
def draw_character(self, encoder, row, col, char, fg_color, bg_color):
    """Draw one character - requires 100+ lines across multiple methods"""
    
    # 1. Get glyph from texture atlas (20 lines)
    glyph_info = self.font_atlas.get_glyph(char)
    if not glyph_info:
        # Handle missing glyph, generate texture, update atlas...
        glyph_info = self._generate_and_cache_glyph(char)
    
    # 2. Create vertex data for background quad (15 lines)
    bg_vertices = self._create_quad_vertices(
        row, col, self.char_width, self.char_height, bg_color
    )
    
    # 3. Create vertex data for character quad (15 lines)
    char_vertices = self._create_textured_quad_vertices(
        row, col, glyph_info.tex_coords, fg_color
    )
    
    # 4. Update vertex buffers (10 lines)
    self._update_vertex_buffer(self.bg_buffer, bg_vertices)
    self._update_vertex_buffer(self.char_buffer, char_vertices)
    
    # 5. Set pipeline state (5 lines)
    encoder.setRenderPipelineState_(self.pipeline_state)
    
    # 6. Set vertex buffers (5 lines)
    encoder.setVertexBuffer_offset_atIndex_(self.bg_buffer, 0, 0)
    encoder.setVertexBuffer_offset_atIndex_(self.char_buffer, 0, 1)
    
    # 7. Set texture (5 lines)
    encoder.setFragmentTexture_atIndex_(self.font_atlas.texture, 0)
    
    # 8. Draw (5 lines)
    encoder.drawPrimitives_vertexStart_vertexCount_(MTLPrimitiveTypeTriangle, 0, 6)

# Plus supporting methods:
# - _generate_and_cache_glyph() - 30 lines
# - _create_quad_vertices() - 20 lines
# - _create_textured_quad_vertices() - 25 lines
# - _update_vertex_buffer() - 15 lines
```

**Total: 100+ lines across multiple methods**

## 2. Font Texture Atlas

### Core Graphics: Not Needed ✅

```python
# No texture atlas needed!
# Core Graphics renders text directly from font files
```

**Total: 0 lines**

### Metal: Required ❌

```python
class FontAtlas:
    """Manage font texture atlas - 200+ lines"""
    
    def __init__(self, font, device):
        self.font = font
        self.device = device
        self.glyphs = {}
        self.texture = None
        self.atlas_width = 2048
        self.atlas_height = 2048
        self.current_x = 0
        self.current_y = 0
        self.row_height = 0
        
    def get_glyph(self, char):
        """Get glyph from atlas or generate it"""
        if char not in self.glyphs:
            self._generate_glyph(char)
        return self.glyphs[char]
    
    def _generate_glyph(self, char):
        """Render character to bitmap and add to atlas"""
        # 1. Create bitmap context (10 lines)
        # 2. Render character to bitmap (15 lines)
        # 3. Find space in atlas (20 lines)
        # 4. Copy bitmap to atlas texture (15 lines)
        # 5. Update texture on GPU (10 lines)
        # 6. Store glyph info (5 lines)
        pass  # 75+ lines of implementation
    
    def _pack_glyph(self, width, height):
        """Find space in atlas for new glyph"""
        # Implement bin packing algorithm
        # Handle atlas full condition
        # Possibly create new atlas texture
        pass  # 40+ lines
    
    def _update_texture(self, x, y, width, height, data):
        """Update GPU texture with new glyph data"""
        # Create texture region
        # Copy data to GPU
        # Handle texture format conversion
        pass  # 30+ lines
```

**Total: 200+ lines**

## 3. Shader Code

### Core Graphics: Not Needed ✅

```python
# No shaders needed!
# Core Graphics handles all rendering
```

**Total: 0 lines**

### Metal: Required ❌

```metal
// Vertex Shader - 30 lines
#include <metal_stdlib>
using namespace metal;

struct VertexIn {
    float2 position [[attribute(0)]];
    float2 texCoord [[attribute(1)]];
    float4 color [[attribute(2)]];
};

struct VertexOut {
    float4 position [[position]];
    float2 texCoord;
    float4 color;
};

vertex VertexOut vertex_main(VertexIn in [[stage_in]],
                             constant float4x4 &mvpMatrix [[buffer(1)]]) {
    VertexOut out;
    out.position = mvpMatrix * float4(in.position, 0.0, 1.0);
    out.texCoord = in.texCoord;
    out.color = in.color;
    return out;
}

// Fragment Shader - 20 lines
fragment float4 fragment_main(VertexOut in [[stage_in]],
                              texture2d<float> texture [[texture(0)]],
                              sampler textureSampler [[sampler(0)]]) {
    float4 texColor = texture.sample(textureSampler, in.texCoord);
    return texColor * in.color;
}

// Plus shader compilation and pipeline setup - 50+ lines in Python
```

**Total: 100+ lines (shader + setup)**

## 4. Initialization

### Core Graphics: Simple ✅

```python
def initialize(self):
    """Initialize Core Graphics backend - 30 lines"""
    # Create font
    self.font = NSFont.fontWithName_size_(self.font_name, self.font_size)
    
    # Calculate character dimensions
    test_string = NSAttributedString.alloc().initWithString_attributes_(
        "M", {NSFontAttributeName: self.font}
    )
    size = test_string.size()
    self.char_width = int(size.width)
    self.char_height = int(size.height * 1.2)
    
    # Create window
    self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        frame, style_mask, NSBackingStoreBuffered, False
    )
    
    # Create view
    self.view = TTKView.alloc().initWithFrame_backend_(frame, self)
    self.window.setContentView_(self.view)
    self.window.makeKeyAndOrderFront_(None)
    
    # Initialize grid
    self.grid = [[(' ', 0, 0) for _ in range(self.cols)] 
                 for _ in range(self.rows)]
```

**Total: 30 lines**

### Metal: Complex ❌

```python
def initialize(self):
    """Initialize Metal backend - 150+ lines"""
    # 1. Create Metal device (10 lines)
    self.device = MTLCreateSystemDefaultDevice()
    if not self.device:
        raise RuntimeError("Metal not available")
    
    # 2. Create command queue (5 lines)
    self.command_queue = self.device.newCommandQueue()
    
    # 3. Load and compile shaders (30 lines)
    shader_source = self._load_shader_source()
    library = self.device.newLibraryWithSource_options_error_(shader_source, None, None)
    vertex_function = library.newFunctionWithName_("vertex_main")
    fragment_function = library.newFunctionWithName_("fragment_main")
    
    # 4. Create render pipeline (25 lines)
    pipeline_descriptor = MTLRenderPipelineDescriptor.alloc().init()
    pipeline_descriptor.setVertexFunction_(vertex_function)
    pipeline_descriptor.setFragmentFunction_(fragment_function)
    # ... configure vertex descriptors, color attachments, etc.
    self.pipeline_state = self.device.newRenderPipelineStateWithDescriptor_error_(
        pipeline_descriptor, None
    )
    
    # 5. Create vertex buffers (20 lines)
    self.vertex_buffer = self.device.newBufferWithLength_options_(
        buffer_size, MTLResourceStorageModeShared
    )
    
    # 6. Create font texture atlas (10 lines + 200 lines in FontAtlas class)
    self.font_atlas = FontAtlas(self.font, self.device)
    self.font_atlas.initialize()
    
    # 7. Create Metal view (15 lines)
    self.metal_view = MTKView.alloc().initWithFrame_device_(frame, self.device)
    self.metal_view.setColorPixelFormat_(MTLPixelFormatBGRA8Unorm)
    # ... configure view
    
    # 8. Create window (15 lines)
    self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        frame, style_mask, NSBackingStoreBuffered, False
    )
    self.window.setContentView_(self.metal_view)
    
    # 9. Initialize grid (5 lines)
    self.grid = [[(' ', 0, 0) for _ in range(self.cols)] 
                 for _ in range(self.rows)]
```

**Total: 150+ lines (plus 200+ for FontAtlas)**

## 5. Rendering Loop

### Core Graphics: Simple ✅

```python
def refresh(self):
    """Refresh display - 1 line"""
    self.view.setNeedsDisplay_(True)

# In TTKView.drawRect_:
def drawRect_(self, rect):
    """Draw the grid - 30 lines"""
    ctx = NSGraphicsContext.currentContext().CGContext()
    
    for row in range(self.backend.rows):
        for col in range(self.backend.cols):
            char, color_pair, attrs = self.backend.grid[row][col]
            
            if char == ' ' and color_pair == 0:
                continue
            
            # Get colors
            fg_rgb, bg_rgb = self.backend.color_pairs.get(color_pair, ...)
            
            # Calculate position
            x = col * self.backend.char_width
            y = (self.backend.rows - row - 1) * self.backend.char_height
            
            # Draw background
            bg_color = NSColor.colorWithRed_green_blue_alpha_(...)
            bg_color.set()
            NSRectFill(NSMakeRect(x, y, width, height))
            
            # Draw character
            attr_string = NSAttributedString.alloc().initWithString_attributes_(
                char, {NSFontAttributeName: font, NSForegroundColorAttributeName: fg_color}
            )
            attr_string.drawAtPoint_(NSMakePoint(x, y))
```

**Total: 30 lines**

### Metal: Complex ❌

```python
def refresh(self):
    """Refresh display - 80+ lines"""
    # 1. Get drawable (5 lines)
    drawable = self.metal_view.currentDrawable()
    if not drawable:
        return
    
    # 2. Create command buffer (5 lines)
    command_buffer = self.command_queue.commandBuffer()
    
    # 3. Create render pass (10 lines)
    render_pass = self.metal_view.currentRenderPassDescriptor()
    encoder = command_buffer.renderCommandEncoderWithDescriptor_(render_pass)
    
    # 4. Set pipeline state (5 lines)
    encoder.setRenderPipelineState_(self.pipeline_state)
    
    # 5. Build vertex data for all characters (30 lines)
    vertices = []
    for row in range(self.rows):
        for col in range(self.cols):
            char, color_pair, attrs = self.grid[row][col]
            if char == ' ' and color_pair == 0:
                continue
            
            # Get glyph from atlas
            glyph = self.font_atlas.get_glyph(char)
            
            # Create vertices for this character
            char_vertices = self._create_character_vertices(
                row, col, glyph, color_pair, attrs
            )
            vertices.extend(char_vertices)
    
    # 6. Update vertex buffer (10 lines)
    vertex_data = struct.pack(...)  # Pack vertex data
    self.vertex_buffer.contents()[0:len(vertex_data)] = vertex_data
    
    # 7. Set buffers and textures (10 lines)
    encoder.setVertexBuffer_offset_atIndex_(self.vertex_buffer, 0, 0)
    encoder.setFragmentTexture_atIndex_(self.font_atlas.texture, 0)
    
    # 8. Draw (5 lines)
    encoder.drawPrimitives_vertexStart_vertexCount_(
        MTLPrimitiveTypeTriangle, 0, len(vertices)
    )
    
    # 9. End encoding and present (5 lines)
    encoder.endEncoding()
    command_buffer.presentDrawable_(drawable)
    command_buffer.commit()
```

**Total: 80+ lines**

## 6. Unicode and Emoji Support

### Core Graphics: Automatic ✅

```python
# Unicode and emoji work automatically!
# Just pass the character to NSAttributedString

def draw_text(self, row, col, text, color_pair, attrs):
    """Works with any Unicode character, including emoji"""
    for i, char in enumerate(text):
        # This works for:
        # - ASCII: 'A', 'b', '1'
        # - Latin Extended: 'é', 'ñ', 'ü'
        # - CJK: '中', '日', '한'
        # - Emoji: '😀', '🎉', '👍'
        # - Complex scripts: Arabic, Thai, etc.
        self.grid[row][col + i] = (char, color_pair, attrs)
```

**Total: 0 extra lines needed**

### Metal: Manual Implementation ❌

```python
class FontAtlas:
    """Must handle Unicode manually - 100+ extra lines"""
    
    def __init__(self):
        # Need separate handling for different Unicode ranges
        self.ascii_glyphs = {}      # U+0000 to U+007F
        self.latin_glyphs = {}      # U+0080 to U+00FF
        self.cjk_glyphs = {}        # U+4E00 to U+9FFF
        self.emoji_glyphs = {}      # U+1F600 to U+1F64F
        # ... many more ranges
    
    def get_glyph(self, char):
        """Must determine which range and handle accordingly"""
        code_point = ord(char)
        
        if code_point < 0x80:
            return self._get_ascii_glyph(char)
        elif code_point < 0x100:
            return self._get_latin_glyph(char)
        elif 0x4E00 <= code_point <= 0x9FFF:
            return self._get_cjk_glyph(char)
        elif 0x1F600 <= code_point <= 0x1F64F:
            return self._get_emoji_glyph(char)
        # ... handle many more ranges
    
    def _get_emoji_glyph(self, char):
        """Emoji are especially difficult"""
        # Emoji are often multi-codepoint (skin tones, etc.)
        # Emoji are colored (need separate texture handling)
        # Emoji sizes vary
        # Must handle emoji sequences
        pass  # 50+ lines of complex logic
```

**Total: 100+ extra lines**

## Summary Table

| Feature | Core Graphics | Metal |
|---------|--------------|-------|
| **Draw Character** | 10 lines | 100+ lines |
| **Font Atlas** | 0 lines (not needed) | 200+ lines |
| **Shaders** | 0 lines (not needed) | 100+ lines |
| **Initialization** | 30 lines | 350+ lines |
| **Rendering Loop** | 30 lines | 80+ lines |
| **Unicode/Emoji** | 0 lines (automatic) | 100+ lines |
| **TOTAL** | ~70 lines | ~930+ lines |

## Complexity Multiplier

**Metal is 13x more complex than Core Graphics for character-grid rendering.**

## Conclusion

The code comparison clearly shows:

1. **Core Graphics is dramatically simpler** - 70 vs 930+ lines
2. **Metal requires extensive infrastructure** - shaders, texture atlas, vertex buffers
3. **Core Graphics handles text automatically** - Unicode, emoji, complex scripts
4. **Metal requires manual implementation** - of everything Core Graphics does automatically

**For TTK's character-grid rendering, Core Graphics is the obvious choice.**

## See Also

- [Backend Decision Summary](BACKEND_DECISION_SUMMARY.md)
- [Full Recommendation](DESKTOP_BACKEND_RECOMMENDATION.md)
- [Core Graphics Proof of Concept](CORE_GRAPHICS_POC.md)
