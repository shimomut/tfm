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
- **ALL documentation files** (*.md) should be placed in the `/doc` directory
- Feature documentation: `doc/FEATURE_NAME_FEATURE.md`
- Implementation summaries: `doc/FEATURE_NAME_IMPLEMENTATION.md`
- System documentation: `doc/SYSTEM_NAME_SYSTEM.md`
- Component documentation: `doc/COMPONENT_NAME_COMPONENT.md`
- Integration guides: `doc/INTEGRATION_NAME_INTEGRATION.md`

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

### Root Directory
- **Project-level files** only
- Main entry point: `tfm.py`
- Build configuration: `setup.py`, `Makefile`
- Project metadata: `README.md`, `requirements.txt`, `.gitignore`
- Temporary summary files are acceptable but should be moved to `doc/` when finalized

## File Placement Rules

### When Creating New Files

1. **Test files** → Always use `test/test_<feature_name>.py`
2. **Documentation** → Always use `doc/<FEATURE_NAME>_<TYPE>.md`
3. **Demo scripts** → Always use `demo/demo_<feature_name>.py`
4. **External tools** → Always use `tools/<tool_name>.<ext>`
5. **Source code** → Always use `src/tfm_<module_name>.py`

### When Moving Existing Files

- If you find files in the wrong location, suggest moving them to the correct directory
- Maintain the same filename but update the path
- Update any imports or references to the moved files

### Examples

#### Correct Placement
```
test/test_remote_log_monitoring.py          # Test file
doc/REMOTE_LOG_MONITORING_FEATURE.md        # Documentation
demo/demo_remote_log.py                     # Demo script
tools/log_analyzer.py                       # External tool
src/tfm_log_manager.py                      # Source code
```

#### Incorrect Placement (to be avoided)
```
remote_log_test.py                          # Should be in test/
REMOTE_LOG_DOCS.md                          # Should be in doc/
log_demo.py                                 # Should be in demo/
analyze_logs.sh                             # Should be in tools/
```

## Migration Guidelines

When working with existing files that are in the wrong location:

1. **Identify misplaced files** during development
2. **Suggest relocation** to the appropriate directory
3. **Update imports and references** after moving files
4. **Test functionality** after file moves to ensure nothing breaks

## Benefits of This Structure

- **Clear organization** - Easy to find files by purpose
- **Scalable** - Structure supports project growth
- **Standard conventions** - Follows Python project best practices
- **Tool-friendly** - IDEs and build tools work better with organized structure
- **Maintainable** - Easier to maintain and navigate the codebase