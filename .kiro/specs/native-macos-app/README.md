# Native macOS App Bundle Specification

## Overview

This specification defines a native macOS application bundle for TFM (Terminal File Manager) using Objective-C to embed Python and launch TFM with its CoreGraphics backend. This approach replaces the unreliable py2app solution with a robust, maintainable native implementation.

## Key Features

- **Native Objective-C launcher** - Minimal code that embeds Python interpreter
- **Embedded Python runtime** - Self-contained Python.framework in app bundle
- **Full Dock integration** - Right-click menu, window list, multi-window support
- **Command-line buildable** - No Xcode IDE required, uses Command Line Tools only
- **Development mode preserved** - Can still run `python3 tfm.py` for fast iteration
- **CoreGraphics backend** - Native macOS desktop UI with NSWindow

## Architecture

```
TFM.app
├── Objective-C Launcher (NSApplication, Python/C API)
├── Embedded Python Runtime (Python.framework + packages)
└── TFM Application (Python source with CoreGraphics backend)
```

The Objective-C launcher creates NSApplication and embeds Python, which then creates TFM windows using the existing CoreGraphics backend. Both layers share the same NSApplication instance through PyObjC.

## Documents

- **requirements.md** - Complete requirements with EARS patterns and acceptance criteria
- **design.md** - Detailed architecture, components, and implementation design
- **tasks.md** - Step-by-step implementation plan with 23 major tasks, 75+ subtasks

## Key Design Decisions

### Why Objective-C?

- Direct C interop with Python/C API (no bridging needed)
- Native macOS APIs (perfect AppKit/Cocoa integration)
- Minimal build complexity (just compile .m files)
- No Xcode IDE required (command-line tools sufficient)
- Smallest binary size (no Swift runtime)

### NSApplication Sharing

The NSApplication instance created in Objective-C is automatically shared with Python through PyObjC:

```objective-c
// Objective-C
NSApplication *app = [NSApplication sharedApplication];
```

```python
# Python (same instance!)
from Cocoa import NSApplication
app = NSApplication.sharedApplication()
```

This allows TFM's CoreGraphics backend to create NSWindow objects that integrate seamlessly with the app's Dock menu and lifecycle.

### Event Loop

The Objective-C launcher starts the NSApplication event loop with `[NSApp run]`, and Python code runs within that loop. No separate event loop is needed in Python.

### Development Workflow

The app bundle is completely separate from source code:

**Development (fast iteration):**
```bash
python3 tfm.py              # Terminal mode
python3 tfm.py --desktop    # Desktop mode
```

**Production (build when ready):**
```bash
cd macos_app
./build.sh
# Creates TFM.app with embedded Python + source
```

## Implementation Status

- [x] Requirements defined (18 requirements with acceptance criteria)
- [x] Design completed (architecture, components, interfaces)
- [x] Tasks planned (23 major tasks, 75+ subtasks)
- [x] Core implementation (Objective-C launcher, Python embedding, build system)
- [x] Bundle optimization (unnecessary files cleanup, ~12.7MB savings total)
- [x] Python pre-compilation (faster startup, consistent performance)
- [x] TTK library optimization (selective file copying, ~12.3MB savings)
- [x] Documentation (build guide, cleanup guide, pre-compilation guide)
- [ ] Final testing and distribution

## Next Steps

1. Review the requirements document
2. Review the design document
3. Review the tasks document
4. Begin implementation starting with task 1

## Requirements Summary

Key requirements include:

1. **Objective-C launcher** with Python/C API embedding
2. **Embedded Python** interpreter (3.9+) in app bundle
3. **TFM source bundling** with all dependencies
4. **CoreGraphics backend** integration
5. **macOS bundle structure** (Contents/MacOS, Resources, Frameworks)
6. **Application icon** and metadata (Info.plist)
7. **Dock integration** with right-click menu
8. **Multi-window support** from Dock menu
9. **Command-line build** system (no Xcode IDE)
10. **Development mode** preservation (python3 tfm.py)
11. **Python dependencies** bundled correctly
12. **Error handling** with native dialogs
13. **Build artifacts** properly organized
14. **Application lifecycle** management
15. **Code signing** support (optional)
16. **Documentation** and examples
17. **Bundle size optimization** (~400KB savings)
18. **Python pre-compilation** (faster startup)

## Testing Strategy

- **Unit tests** for Objective-C components
- **Property-based tests** for correctness properties
- **Integration tests** for bundle structure and Python embedding
- **Manual testing** for Dock integration and multi-window support

## Build Requirements

- macOS 10.13 or later
- Xcode Command Line Tools (`xcode-select --install`)
- Python 3.9 or later
- PyObjC framework

## Success Criteria

The implementation is successful when:

1. ✅ TFM.app launches and displays CoreGraphics UI
2. ✅ Dock integration works (right-click menu, window list)
3. ✅ Multiple windows can be opened and work independently
4. ✅ Development mode still works (python3 tfm.py)
5. ✅ Build is command-line only (no Xcode IDE needed)
6. ✅ Error handling shows clear messages
7. ✅ App bundle is self-contained and portable

## Timeline Estimate

- **Phase 1: Core launcher** (Tasks 1-6) - 2-3 days
- **Phase 2: Window management** (Tasks 7-10) - 2-3 days
- **Phase 3: Build system** (Tasks 11-14) - 2-3 days
- **Phase 4: Polish** (Tasks 15-20) - 1-2 days

**Total: 7-11 days** for complete implementation

## References

- [Python/C API Documentation](https://docs.python.org/3/c-api/)
- [PyObjC Documentation](https://pyobjc.readthedocs.io/)
- [macOS App Bundle Structure](https://developer.apple.com/library/archive/documentation/CoreFoundation/Conceptual/CFBundles/BundleTypes/BundleTypes.html)
- [NSApplication Documentation](https://developer.apple.com/documentation/appkit/nsapplication)
