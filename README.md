# TFM - TUI File Manager

A powerful terminal-based file manager built with Python's curses library. Navigate your filesystem with keyboard shortcuts in a clean, intuitive dual-pane interface with comprehensive file operations, advanced text editing, and professional-grade features.

## Key Features

- **Dual-pane interface** with independent navigation and cross-pane operations
- **Advanced search** with real-time filtering and background processing  
- **Multi-selection** with bulk operations and progress tracking
- **Built-in text viewer** with syntax highlighting for 20+ file formats
- **External program integration** with configurable launchers
- **AWS S3 support** for cloud storage operations
- **Customizable interface** with multiple color schemes and key bindings
- **Remote log monitoring** for debugging and system monitoring

## Development with Kiro

This application was developed using [Kiro](https://kiro.dev/) heavily - an AI-powered development assistant. Approximately 99% of the code was auto-generated from natural language based interactive chat sessions, demonstrating the power of AI-assisted development for creating complex, feature-rich applications.

## Screenshots

![main screen](doc/images/main-screen.png)

<div align="center">
<img src="doc/images/incremental-search.png" alt="incremental search" width="250">
<img src="doc/images/favorite-directories.png" alt="favorite directories" width="250">
<img src="doc/images/grep-dialog.png" alt="grep dialog" width="250">
<img src="doc/images/search-dialog.png" alt="search dialog" width="250">
<img src="doc/images/batch-rename.png" alt="batch rename" width="250">
<img src="doc/images/text-viewer.png" alt="built-in text viewer" width="250">
<img src="doc/images/external-programs.png" alt="external programs" width="250">
<img src="doc/images/color-schemes.png" alt="color schemes" width="250">
</div>


## Quick Start

### Installation
1. Ensure you have Python 3.6+ installed
2. Clone or download TFM
3. Run the file manager:
   ```bash
   python3 tfm.py
   ```

### Essential Controls
- **Navigate:** `↑↓` to move up/down, `←→` to switch panes/navigate directories
- **Select:** `Space` to select/deselect files, `a` for all files, `A` for all items
- **File operations:** `c/C` (copy), `m/M` (move), `k/K` (delete), `r/R` (rename)
- **Help:** `?` for comprehensive help dialog
- **Quit:** `q/Q` to exit

### Help System
Press `?` to open the comprehensive help dialog with all key bindings and features organized by category. The help dialog is your quick reference guide - no need to memorize all shortcuts!

## Documentation

For comprehensive information about TFM's features and usage:

### User Documentation
- **[Complete User Guide](doc/TFM_USER_GUIDE.md)** - Comprehensive guide covering all features, configuration, and usage
- **[Remote Log Monitoring](doc/REMOTE_LOG_MONITORING_FEATURE.md)** - Real-time log monitoring setup and usage
- **[Search Animation](doc/SEARCH_ANIMATION_FEATURE.md)** - Advanced search features and visual feedback

### Developer Documentation
- **[Navigation System](doc/dev/NAVIGATION_SYSTEM.md)** - Core navigation implementation
- **[Remote Log Implementation](doc/dev/REMOTE_LOG_MONITORING_IMPLEMENTATION.md)** - Technical details of log monitoring
- **[External Programs](doc/dev/EXTERNAL_PROGRAMS_IMPLEMENTATION.md)** - Program integration system

## Key Features Overview

All key bindings are fully customizable through the configuration system. For complete key binding reference, press `?` in TFM or see the [User Guide](doc/TFM_USER_GUIDE.md).

### Core Operations
- **Navigation:** Arrow keys, Tab to switch panes, Enter to open directories/files
- **File Operations:** Copy (`c/C`), Move (`m/M`), Delete (`k/K`), Rename (`r/R`)
- **Selection:** Space to select files, `a` for all files, `A` for all items
- **Search:** `f` for incremental search, `F` for filename search, `G` for content search
- **Archives:** `p/P` to create archives, `u/U` to extract
- **Text Viewer:** `v/V` to view files with syntax highlighting

### Advanced Features
- **Favorite Directories:** `j` for quick access to bookmarked locations
- **External Programs:** `x` for custom program integration
- **Sub-shell Mode:** `X` to enter shell with TFM environment variables
- **Configuration:** `Z` for settings menu
- **AWS S3 Support:** Navigate S3 buckets using `s3://bucket/path` syntax

## Built-in Text Viewer

TFM includes a powerful text viewer with syntax highlighting for 20+ file formats. Press `Enter` on text files or use `v` to open the viewer.

**Features:**
- Syntax highlighting for Python, JavaScript, JSON, Markdown, YAML, and more
- Line numbers, horizontal scrolling, search functionality
- Multiple encoding support (UTF-8, Latin-1, CP1252)

**Enhanced highlighting:** Install `pygments` for full syntax support:
```bash
pip install pygments
```

## Sub-shell Mode

Press `X` to temporarily suspend TFM and enter a shell with environment variables providing access to current directories and selected files:

- `TFM_LEFT_DIR`, `TFM_RIGHT_DIR` - Directory paths for each pane
- `TFM_THIS_DIR`, `TFM_OTHER_DIR` - Current and other pane directories  
- `TFM_LEFT_SELECTED`, `TFM_RIGHT_SELECTED` - Selected files in each pane
- `TFM_ACTIVE` - Set to '1' to indicate TFM sub-shell mode

Type `exit` to return to TFM.

## Advanced Features

- **Batch Rename:** Regex-based renaming with capture groups and macros
- **Threaded Search:** Non-blocking filename and content search with progress tracking
- **Pane Management:** Resizable layout, directory sync, state persistence
- **External Integration:** VSCode, Beyond Compare, and custom program support
- **Remote Log Monitoring:** Stream logs to remote terminals for debugging
- **AWS S3 Support:** Navigate and manage S3 buckets with seamless local/remote operations

For detailed information on all features, see the [User Guide](doc/TFM_USER_GUIDE.md).

## Command Line Options

```bash
# Specify startup directories
python3 tfm.py --left /path/to/projects --right /path/to/documents

# Enable remote log monitoring
python3 tfm.py --remote-log-port 8888

# Combined usage
python3 tfm.py --left ./src --right ./test --remote-log-port 8888

# Help and version
python3 tfm.py --help
python3 tfm.py --version
```

## Installation

### Requirements
- Python 3.6+ with curses library (built-in on Unix systems)
- Terminal with curses support

### Optional Dependencies
```bash
pip install pygments  # Enhanced syntax highlighting
pip install boto3     # AWS S3 support
```

### Installation Options
```bash
# Run directly
python3 tfm.py

# Install from source
python3 setup.py install
tfm
```

## Configuration

TFM is highly configurable through `~/.tfm/config.py`. Access configuration via the Settings menu (`Z` key) or edit manually.

**Key areas:**
- Color schemes and display preferences
- Key bindings (fully customizable)
- External programs and text editor
- Favorite directories and startup paths
- Performance and behavior settings

For detailed configuration options, see the [User Guide](doc/TFM_USER_GUIDE.md#configuration).

## Project Structure

```
tfm/
├── src/           # Core application code
├── test/          # Test files and demos
├── doc/           # User documentation
├── doc/dev/       # Developer documentation
├── tools/         # External integration scripts
├── demo/          # Interactive demonstrations
└── tfm.py         # Main entry point
```

## Remote Log Monitoring

Monitor TFM operations remotely for debugging:

```bash
# Start TFM with remote log monitoring
python3 tfm.py --remote-log-port 8888

# Connect from another terminal
python3 tools/tfm_log_client.py localhost 8888
```

The log client provides color-coded output for different log sources and handles network connectivity gracefully.

## Troubleshooting

**Installation Issues:**
- Ensure Python 3.6+ is installed
- Check terminal compatibility with curses library

**Performance Issues:**
- Install `pygments` for better text viewer performance
- Check available memory for large directory operations

For detailed troubleshooting, see the [User Guide](doc/TFM_USER_GUIDE.md#troubleshooting).

## Contact Author

Have questions, suggestions, or found a bug? Get in touch:

- **GitHub Repository**: [https://github.com/shimomut/tfm](https://github.com/shimomut/tfm)
- **GitHub Issues**: [Report bugs or request features](https://github.com/shimomut/tfm/issues)
- **Author's X (Twitter)**: [@smmrtmnr](https://x.com/smmrtmnr)

We welcome feedback and contributions to make TFM even better!

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues:** Create an issue on the project repository
- **Documentation:** Review files in `doc/` and `doc/dev/` directories
- **User Guide:** See [TFM_USER_GUIDE.md](doc/TFM_USER_GUIDE.md) for comprehensive information