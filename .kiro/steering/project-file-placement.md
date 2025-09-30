---
inclusion: always
---

# TFM Project File Placement Rules

## Directory Structure Guidelines

This project follows a clean directory structure that separates different types of files. Always place files in the appropriate directory based on their purpose.

### Test Files (`test/`)
- **ALL test files** must be placed in the `/test` directory
- Test files should follow the naming convention `test_*.py`
- Integration tests: `test/test_integration_*.py`
- Unit tests: `test/test_unit_*.py`
- Demo test files: `test/demo_*.py`
- Verification scripts: `test/verify_*.py`

### Documentation (`doc/`)
- **End-user documentation** should be placed in the `/doc` directory
- **Developer documentation** should be placed in the `/doc/dev` directory

#### End-User Documentation (`doc/`)
- User guides: `doc/USER_GUIDE.md`, `doc/INSTALLATION_GUIDE.md`
- Feature documentation: `doc/FEATURE_NAME_FEATURE.md`
- Integration guides: `doc/INTEGRATION_NAME_INTEGRATION.md`
- Feature summaries: `doc/FEATURE_SUMMARY.md`

#### Developer Documentation (`doc/dev/`)
- System documentation: `doc/dev/SYSTEM_NAME_SYSTEM.md`
- Component documentation: `doc/dev/COMPONENT_NAME_COMPONENT.md`
- Implementation summaries: `doc/dev/FEATURE_NAME_IMPLEMENTATION.md`
- Architecture documentation: `doc/dev/PROJECT_STRUCTURE.md`
- Technical specifications: `doc/dev/CORE_COMPONENTS.md`

#### Documentation Categorization Guidelines

**End-User Documentation** (`doc/`) - Documents that help users understand and use TFM:
- Installation and setup guides
- User guides and tutorials
- Feature descriptions from user perspective
- Integration guides for external tools
- Configuration examples and options

**Developer Documentation** (`doc/dev/`) - Documents that help developers understand and modify TFM:
- System architecture and design
- Component implementation details
- Code organization and structure
- Technical specifications
- Internal APIs and interfaces
- Development processes and guidelines

### Demo Files (`demo/`)
- **ALL demo and example files** should be placed in the `/demo` directory
- Demo scripts: `demo/demo_*.py`
- Example configurations: `demo/example_*.py`
- Interactive demonstrations: `demo/interactive_*.py`
- Sample data files: `demo/sample_*`

### External Tools (`tools/`)
- **ALL external programs and scripts** should be placed in the `/tools` directory
- Shell scripts: `tools/*.sh`
- Python utility scripts: `tools/*.py`
- Configuration scripts: `tools/config_*.py`
- Wrapper scripts: `tools/*_wrapper.sh`
- Build and deployment scripts: `tools/build_*.sh`, `tools/deploy_*.sh`

### Source Code (`src/`)
- **Core application code** only
- Main modules: `src/tfm_*.py`
- Configuration templates: `src/_config.py`

### Temporary Files (`temp/`)
- **ALL temporary files** should be placed in the `/temp` directory
- Temporary documentation files: `temp/TEMP_FEATURE_DOCS.md`
- Temporary test programs: `temp/temp_test_*.py`
- Refactoring verification scripts: `temp/verify_refactoring_*.py`
- Bug-fix test programs: `temp/test_bugfix_*.py`
- Work-in-progress files that will be moved to proper locations when complete
- Files created during development that are not needed after completion

### Root Directory
- **Project-level files** only
- Main entry point: `tfm.py`
- Build configuration: `setup.py`, `Makefile`
- Project metadata: `README.md`, `requirements.txt`, `.gitignore`
- **No temporary files** - these should be in `temp/` directory

## File Placement Rules

### When Creating New Files

1. **Test files** → Always use `test/test_<feature_name>.py`
2. **End-user documentation** → Always use `doc/<FEATURE_NAME>_<TYPE>.md`
3. **Developer documentation** → Always use `doc/dev/<SYSTEM_NAME>_<TYPE>.md`
4. **Demo scripts** → Always use `demo/demo_<feature_name>.py`
5. **External tools** → Always use `tools/<tool_name>.<ext>`
6. **Source code** → Always use `src/tfm_<module_name>.py`
7. **Temporary files** → Always use `temp/<temp_file_name>.<ext>`

### When Moving Existing Files

- If you find files in the wrong location, suggest moving them to the correct directory
- Maintain the same filename but update the path
- Update any imports or references to the moved files

### Examples

#### Correct Placement
```
test/test_remote_log_monitoring.py          # Test file
doc/REMOTE_LOG_MONITORING_FEATURE.md        # End-user feature documentation
doc/dev/LOG_MANAGER_SYSTEM.md               # Developer system documentation
demo/demo_remote_log.py                     # Demo script
tools/log_analyzer.py                       # External tool
src/tfm_log_manager.py                      # Source code
temp/temp_refactoring_test.py               # Temporary test program
temp/TEMP_FEATURE_ANALYSIS.md               # Temporary documentation
```

#### Incorrect Placement (to be avoided)
```
remote_log_test.py                          # Should be in test/
REMOTE_LOG_DOCS.md                          # Should be in doc/ (end-user) or doc/dev/ (developer)
log_demo.py                                 # Should be in demo/
analyze_logs.sh                             # Should be in tools/
TEMP_REFACTORING_SUMMARY.md                 # Should be in temp/
verify_bugfix.py                            # Should be in temp/
SYSTEM_DOCS.md                              # Should be in doc/dev/ (not doc/)
```

## Temporary File Guidelines

### When to Use `temp/` Directory

- **Refactoring verification**: Test programs created to verify refactoring works correctly
- **Bug-fix testing**: Temporary test scripts to reproduce and verify bug fixes
- **Work-in-progress documentation**: Draft documentation files being developed
- **Experimental code**: Code being tested before integration into main codebase
- **Development artifacts**: Files created during development that won't be needed long-term

### Temporary File Lifecycle

1. **Create** temporary files in `temp/` during development
2. **Use** them for verification, testing, or experimentation
3. **Clean up** by either:
   - Moving to appropriate permanent location (`test/`, `doc/`, etc.) if keeping
   - Deleting if no longer needed after completion
   - Archiving if needed for future reference

### Naming Conventions for Temporary Files

- Temporary test programs: `temp/temp_test_<feature>.py`
- Refactoring verification: `temp/verify_<refactoring_name>.py`
- Bug-fix testing: `temp/test_bugfix_<issue>.py`
- Temporary docs: `temp/TEMP_<FEATURE>_<TYPE>.md`
- Work-in-progress: `temp/wip_<description>.<ext>`

## Migration Guidelines

When working with existing files that are in the wrong location:

1. **Identify misplaced files** during development
2. **Suggest relocation** to the appropriate directory
3. **Update imports and references** after moving files
4. **Test functionality** after file moves to ensure nothing breaks
5. **Move temporary files** from root directory to `temp/` directory

## Benefits of This Structure

- **Clear organization** - Easy to find files by purpose
- **Scalable** - Structure supports project growth
- **Standard conventions** - Follows Python project best practices
- **Tool-friendly** - IDEs and build tools work better with organized structure
- **Maintainable** - Easier to maintain and navigate the codebase