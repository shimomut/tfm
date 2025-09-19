# TFM Project Structure

## Overview
The TFM (Terminal File Manager) project is organized into a clean directory structure that separates source code, tests, and documentation.

## Directory Structure

```
tfm/
├── src/                    # Source code
│   ├── tfm_main.py        # Main application logic
│   ├── tfm_config.py      # Configuration system
│   ├── tfm_const.py       # Constants and definitions
│   ├── tfm_colors.py      # Color management
│   ├── tfm_text_viewer.py # Text file viewer
│   └── _config.py         # Default configuration template
├── test/                   # Test files and demos
│   ├── test_*.py          # Unit and integration tests
│   ├── demo_*.py          # Interactive demos
│   └── verify_*.py        # Verification scripts
├── doc/                    # Documentation
│   ├── *.md               # Feature documentation
│   └── PROJECT_STRUCTURE.md # This file
├── tfm.py                  # Main entry point
├── setup.py               # Package setup
├── Makefile               # Build automation
├── requirements.txt       # Python dependencies
├── README.md              # Project overview
└── .gitignore             # Git ignore rules
```

## Source Code (`src/`)

### Core Files
- **`tfm_main.py`**: Main application with FileManager class and UI logic
- **`tfm_config.py`**: Configuration management and user settings
- **`tfm_const.py`**: Application constants and key definitions
- **`tfm_colors.py`**: Color scheme and terminal color management
- **`tfm_text_viewer.py`**: Text file viewing functionality
- **`_config.py`**: Template configuration file for users

### Key Components
- **FileManager Class**: Main application controller
- **Configuration System**: User-customizable settings
- **Color Management**: Terminal color support
- **Text Viewer**: Built-in text file viewer
- **Dialog System**: User interaction dialogs

## Tests (`test/`)

### Test Categories
- **Unit Tests** (`test_*.py`): Individual component testing
- **Integration Tests** (`test_*_integration.py`): Feature integration testing
- **Demo Scripts** (`demo_*.py`): Interactive demonstrations
- **Verification Scripts** (`verify_*.py`): Quick feature verification

### Test Files
- `test_delete_integration.py`: Delete functionality tests
- `test_copy_integration.py`: Copy functionality tests
- `test_navigation_keys_removed.py`: Navigation key removal tests
- `test_help_integration.py`: Help system tests
- `demo_delete_feature.py`: Interactive delete demo
- `verify_complete_implementation.py`: Overall verification

## Documentation (`doc/`)

### Documentation Types
- **Feature Documentation**: Detailed feature descriptions
- **Implementation Summaries**: Development progress tracking
- **User Guides**: Usage instructions and examples
- **Technical Specifications**: System design and architecture

### Key Documents
- `DELETE_FEATURE_IMPLEMENTATION.md`: Delete functionality
- `COPY_FEATURE_IMPLEMENTATION.md`: Copy functionality
- `NAVIGATION_KEYS_SIMPLIFICATION.md`: Navigation changes
- `HELP_DIALOG_IMPLEMENTATION_SUMMARY.md`: Help system
- `CONFIGURATION_SYSTEM.md`: Configuration management

## Entry Points

### Main Entry Point
- **`tfm.py`**: Primary executable that sets up paths and launches TFM

### Alternative Entry Points
- **`python -m src.tfm_main`**: Direct module execution
- **`make run`**: Makefile target
- **`python setup.py install && tfm`**: Installed package

## Build System

### Makefile Targets
- `make run`: Run TFM
- `make test`: Run all tests
- `make test-quick`: Quick verification
- `make clean`: Clean temporary files
- `make install`: Install package
- `make dev-install`: Development installation

### Setup Script
- **`setup.py`**: Standard Python package setup
- Supports pip installation
- Defines console script entry point
- Manages dependencies

## Development Workflow

### Adding New Features
1. Implement in `src/` directory
2. Add tests in `test/` directory
3. Document in `doc/` directory
4. Update README.md if needed

### Testing
1. Run individual tests: `python test/test_feature.py`
2. Run all tests: `make test`
3. Quick verification: `make test-quick`

### Documentation
1. Feature docs go in `doc/`
2. Code comments in source files
3. README.md for project overview
4. Update PROJECT_STRUCTURE.md for structural changes

## Dependencies

### Runtime Dependencies
- Python 3.6+
- Standard library modules (curses, pathlib, etc.)

### Development Dependencies
- pytest (optional, for testing)
- flake8 (optional, for linting)
- black (optional, for formatting)

## Configuration

### User Configuration
- Located at `~/.tfm/config.py`
- Created from `src/_config.py` template
- Fully customizable key bindings and settings

### System Configuration
- Default settings in `src/tfm_config.py`
- Constants in `src/tfm_const.py`
- Color schemes in `src/tfm_colors.py`

## Benefits of This Structure

1. **Separation of Concerns**: Clear separation between source, tests, and docs
2. **Easy Navigation**: Logical organization makes finding files simple
3. **Clean Root**: Root directory contains only essential files
4. **Scalability**: Structure supports project growth
5. **Standard Layout**: Follows Python project conventions
6. **Build Automation**: Makefile provides common tasks
7. **Package Ready**: Setup.py enables pip installation

## Migration Notes

### From Flat Structure
- All source files moved to `src/`
- All test files moved to `test/`
- All documentation moved to `doc/`
- Import paths updated in test files
- New entry point created (`tfm.py`)

### Backward Compatibility
- Old import paths still work within `src/`
- Configuration system unchanged
- User settings location unchanged
- All functionality preserved