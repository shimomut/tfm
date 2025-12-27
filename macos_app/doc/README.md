# TFM macOS App Documentation

This directory contains detailed documentation for the TFM macOS application bundle.

## Architecture

- **[SINGLE_PROCESS_ARCHITECTURE.md](SINGLE_PROCESS_ARCHITECTURE.md)** - Complete architecture overview
  - Single-process, single-window design
  - Benefits and trade-offs
  - Process lifecycle
  - Performance considerations

- **[SINGLE_PROCESS_IMPLEMENTATION.md](SINGLE_PROCESS_IMPLEMENTATION.md)** - Implementation details
  - What changed from multi-process approach
  - Code changes and simplifications
  - Testing and verification

## Technical Details

- **[DEPENDENCY_COLLECTION_FIX.md](DEPENDENCY_COLLECTION_FIX.md)** - Dependency management
  - How Python dependencies are collected
  - Virtual environment integration
  - PyObjC framework handling

- **[ENTRY_POINT_FIX.md](ENTRY_POINT_FIX.md)** - Entry point consistency
  - Using `cli_main()` for both CLI and app
  - Backend initialization
  - Argument handling

- **[EXTERNAL_PROGRAMS_FIX.md](EXTERNAL_PROGRAMS_FIX.md)** - External programs execution
  - How external programs work in app bundle
  - `tfm_python` variable for bundled Python
  - Configuration examples

- **[VENV_BASED_BUILD.md](VENV_BASED_BUILD.md)** - Virtual environment based build
  - Build system philosophy
  - Python detection and collection
  - Framework structure creation
  - Benefits and troubleshooting

- **[PYTHON_PRECOMPILATION.md](PYTHON_PRECOMPILATION.md)** - Python pre-compilation
  - Pre-compiling Python source files to bytecode
  - Performance benefits
  - File structure and compatibility
  - Verification and testing

- **[UNNECESSARY_FILES_CLEANUP.md](UNNECESSARY_FILES_CLEANUP.md)** - Unnecessary files cleanup
  - Identification of unnecessary Python files
  - Python.app removal
  - Development tools cleanup
  - Space savings and verification

- **[SYMLINK_FIX.md](SYMLINK_FIX.md)** - Broken symlink fix
  - Problem description and root cause
  - Solution using `ln -sfn` flag
  - Framework structure verification
  - Technical notes on symlink behavior

- **[SYSTEM_INDEPENDENCE.md](SYSTEM_INDEPENDENCE.md)** - System Python independence
  - Verification of no system Python dependencies
  - sitecustomize.py implementation
  - Install name updates
  - External dependencies (gettext)

- **[FONT_RENDERING_FIX.md](FONT_RENDERING_FIX.md)** - Font rendering consistency
  - Font height calculation fix
  - CLI vs app bundle rendering
  - Font metrics approach

## Testing

- **[MANUAL_TEST_GUIDE.md](MANUAL_TEST_GUIDE.md)** - Manual testing procedures
  - Build verification
  - Launch testing
  - Feature testing
  - Error handling verification

- **[INTEGRATION_TEST_RESULTS.md](INTEGRATION_TEST_RESULTS.md)** - Automated test results
  - Build process tests
  - Development mode tests
  - Error handling tests

## Project Status

- **[COMPLETION_SUMMARY.md](COMPLETION_SUMMARY.md)** - Overall project summary
  - What was built
  - Requirements coverage
  - Known limitations
  - Next steps

## Quick Links

- [Main README](../README.md) - Build instructions and quick start
- [Build Script](../build.sh) - Main build automation
- [Source Code](../src/) - Objective-C implementation

