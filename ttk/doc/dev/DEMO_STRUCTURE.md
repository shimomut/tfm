# TTK Demo Structure

## Overview

This document describes the organization of TTK demo applications and the rationale for their placement within the TTK library structure.

## Directory Structure

```
ttk/
├── demo/                    # TTK demo applications
│   ├── __init__.py         # Package initialization
│   └── demo_ttk.py         # Main TTK demo application
├── test/                    # TTK tests
│   └── test_demo_application.py  # Tests for demo application
└── ...
```

## Demo File Placement

### TTK Demo Files (`ttk/demo/`)

All TTK-specific demo files are placed in the `ttk/demo/` directory to:

1. **Maintain Library Independence**: Keep TTK demos separate from TFM application demos
2. **Package Organization**: Demos are part of the TTK package and can be imported as `from ttk.demo import ...`
3. **Clear Separation**: Users can easily distinguish between TTK library examples and TFM application examples
4. **Distribution**: TTK demos can be distributed with the library package

### TFM Demo Files (`demo/`)

TFM-specific demo files remain in the root `demo/` directory for TFM application demonstrations.

## Demo Application Structure

### Main Demo (`ttk/demo/demo_ttk.py`)

The main TTK demo application provides:

- **Command-line Interface**: Backend selection via `--backend` argument
- **Backend Selection Logic**: Auto-detection and manual selection
- **Application Lifecycle**: Initialize, run, shutdown pattern
- **Basic Test Interface**: Simple demonstration of rendering capabilities

### Running the Demo

```bash
# From project root
python ttk/demo/demo_ttk.py --backend curses
python ttk/demo/demo_ttk.py --backend metal  # macOS only
python ttk/demo/demo_ttk.py --backend auto   # Auto-detect

# As a module
python -m ttk.demo.demo_ttk --backend curses
```

## Import Patterns

### Standalone Execution

When run as a standalone script, the demo adds the parent directory to the path:

```python
if __name__ == '__main__':
    parent_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(parent_dir))
```

### Module Import

When imported as a module, standard package imports work:

```python
from ttk.demo.demo_ttk import DemoApplication
```

## Testing

Demo application tests are located in `ttk/test/test_demo_application.py` and verify:

- Backend selection logic
- Command-line argument parsing
- Application lifecycle management
- Error handling

## Future Demo Applications

Additional demo applications should follow the same pattern:

1. Place in `ttk/demo/` directory
2. Follow naming convention: `demo_<feature>.py`
3. Import from ttk package: `from ttk.module import Class`
4. Support both standalone and module execution
5. Include comprehensive tests in `ttk/test/`

## Benefits

- **Clear Organization**: TTK demos are clearly separated from TFM demos
- **Package Distribution**: Demos can be included in TTK package distribution
- **Import Consistency**: Standard Python package import patterns
- **Maintainability**: Easy to locate and update TTK-specific demos
- **Documentation**: Demos serve as working examples for TTK users

## Related Documentation

- [Project File Placement Rules](../../../.kiro/steering/project-file-placement.md)
- [TTK Library Structure](../../README.md)
- [Demo Application Implementation](DEMO_APPLICATION_IMPLEMENTATION.md)
