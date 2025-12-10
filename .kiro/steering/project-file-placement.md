---
inclusion: always
---

# TFM Project File Placement Rules

## Directory Structure Guidelines

This project follows a clean directory structure that separates different types of files. Always place files in the appropriate directory based on their purpose.

### Test Files (`test/`)
- **TFM test files** must be placed in the `/test` directory
- Test files should follow the naming convention `test_*.py`
- Integration tests: `test/test_integration_*.py`
- Unit tests: `test/test_unit_*.py`
- Demo test files: `test/demo_*.py`
- Verification scripts: `test/verify_*.py`

### TTK Library Test Files (`ttk/test/`)
- **TTK-specific test files** must be placed in the `/ttk/test` directory
- This keeps TTK library tests separate from TFM application tests
- Test files should follow the naming convention `test_*.py`
- TTK tests should import from the ttk package: `from ttk.module import Class`
- Example: `ttk/test/test_input_event.py`, `ttk/test/test_renderer_abc.py`

### TTK Library Documentation (`ttk/doc/`)
- **TTK end-user documentation** should be placed in the `/ttk/doc` directory
- **TTK developer documentation** should be placed in the `/ttk/doc/dev` directory
- This keeps TTK library documentation separate from TFM application documentation
- TTK is a standalone library, so its documentation should be self-contained

#### TTK End-User Documentation (`ttk/doc/`)
- Library overview: `ttk/doc/README.md`
- User guides: `ttk/doc/USER_GUIDE.md`
- API reference: `ttk/doc/API_REFERENCE.md`
- Backend implementation guides: `ttk/doc/BACKEND_IMPLEMENTATION_GUIDE.md`
- Usage examples: `ttk/doc/EXAMPLES.md`

#### TTK Developer Documentation (`ttk/doc/dev/`)
- Implementation details: `ttk/doc/dev/COMPONENT_NAME_IMPLEMENTATION.md`
- Architecture documentation: `ttk/doc/dev/ARCHITECTURE.md`
- Technical specifications: `ttk/doc/dev/SPECIFICATION_NAME_SPEC.md`
- Example: `ttk/doc/dev/METAL_INITIALIZATION_IMPLEMENTATION.md`

### TFM Documentation (`doc/`)
- **TFM end-user documentation** should be placed in the `/doc` directory
- **TFM developer documentation** should be placed in the `/doc/dev` directory
- This is for TFM application-specific documentation only

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

## Documentation Generation Policy

### When to Create Documentation

**ALWAYS generate separate documentation for end-users and developers** when creating or updating features that affect both audiences.

#### Dual Documentation Required (Both `doc/` and `doc/dev/`)
Create both end-user and developer documentation when:
- **New user-facing features** - Features that users interact with directly
- **Configuration changes** - Changes that affect user configuration files
- **Behavior changes** - Changes that affect how users experience TFM
- **Integration features** - Features that integrate with external tools users might use
- **API changes** - Changes that affect both user experience and developer implementation

#### Developer Documentation Only (`doc/dev/`)
Create only developer documentation when changes are:
- **Pure implementation details** - Internal code refactoring without user impact
- **Architecture changes** - Internal system design changes
- **Performance optimizations** - Internal improvements that don't change user experience
- **Bug fixes** - Internal fixes that don't change user-facing behavior
- **Code organization** - Moving or restructuring code without functional changes
- **Testing infrastructure** - Changes to test systems and procedures
- **Build system changes** - Changes to development and build processes

#### End-User Documentation Only (`doc/`)
Create only end-user documentation when:
- **Usage guides** - How-to guides that don't require implementation knowledge
- **Configuration examples** - User configuration examples and templates
- **Troubleshooting guides** - User-level problem solving (rare, usually needs both)

### Documentation Content Guidelines

#### End-User Documentation Content
- **What the feature does** - Clear description of functionality
- **How to use it** - Step-by-step usage instructions
- **Configuration** - How to configure and customize
- **Key bindings** - What keys to press
- **What users will see** - Expected behavior and visual feedback
- **Troubleshooting** - Common user problems and solutions
- **Examples** - Practical usage examples
- **Benefits** - Why users would want to use this feature

#### Developer Documentation Content
- **Implementation details** - How the feature is implemented
- **Architecture** - System design and component relationships
- **Code examples** - API usage and integration examples
- **Testing** - How to test the feature and run test suites
- **Technical specifications** - Detailed technical requirements
- **Integration points** - How it connects with other systems
- **Performance considerations** - Memory, CPU, and scalability aspects
- **Future enhancements** - Technical roadmap and planned improvements
- **Troubleshooting** - Developer-level debugging and problem solving

### Documentation Naming Conventions

#### End-User Documents
- Feature documentation: `doc/FEATURE_NAME_FEATURE.md`
- User guides: `doc/USER_GUIDE.md`
- Installation guides: `doc/INSTALLATION_GUIDE.md`
- Integration guides: `doc/TOOL_NAME_INTEGRATION.md`

#### Developer Documents
- Implementation documentation: `doc/dev/FEATURE_NAME_IMPLEMENTATION.md`
- System documentation: `doc/dev/SYSTEM_NAME_SYSTEM.md`
- Architecture documentation: `doc/dev/COMPONENT_NAME_COMPONENT.md`
- Technical specifications: `doc/dev/SPECIFICATION_NAME_SPEC.md`

### Cross-References Between Documents

When creating both end-user and developer documentation:
- **End-user docs** may reference developer docs for advanced customization
- **Developer docs** should reference end-user docs for context and user impact
- Use relative links: `[Implementation Details](dev/FEATURE_NAME_IMPLEMENTATION.md)`

### Examples

#### Dual Documentation Example
**New Search Feature**:
- `doc/SEARCH_FEATURE.md` - How users search for files, key bindings, configuration
- `doc/dev/SEARCH_IMPLEMENTATION.md` - Search algorithms, indexing, performance, API

#### Developer-Only Documentation Example
**Internal Cache Optimization**:
- `doc/dev/CACHE_OPTIMIZATION_IMPLEMENTATION.md` - Technical details of cache improvements
- No end-user doc needed - users don't interact with cache directly

#### End-User-Only Documentation Example (Rare)
**Configuration Template**:
- `doc/CONFIGURATION_EXAMPLES.md` - Example configurations for common use cases
- No developer doc needed - just examples, not implementation

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

1. **TFM test files** → Always use `test/test_<feature_name>.py`
2. **TTK test files** → Always use `ttk/test/test_<feature_name>.py`
3. **TTK end-user documentation** → Always use `ttk/doc/<FEATURE_NAME>_<TYPE>.md`
4. **TTK developer documentation** → Always use `ttk/doc/dev/<COMPONENT_NAME>_<TYPE>.md`
5. **TFM end-user documentation** → Always use `doc/<FEATURE_NAME>_<TYPE>.md`
6. **TFM developer documentation** → Always use `doc/dev/<SYSTEM_NAME>_<TYPE>.md`
7. **Demo scripts** → Always use `demo/demo_<feature_name>.py`
8. **External tools** → Always use `tools/<tool_name>.<ext>`
9. **Source code** → Always use `src/tfm_<module_name>.py`
10. **Temporary files** → Always use `temp/<temp_file_name>.<ext>`

### When Moving Existing Files

- If you find files in the wrong location, suggest moving them to the correct directory
- Maintain the same filename but update the path
- Update any imports or references to the moved files

### Examples

#### Correct Placement
```
test/test_remote_log_monitoring.py          # TFM test file
ttk/test/test_input_event.py                # TTK test file
ttk/doc/API_REFERENCE.md                    # TTK end-user documentation
ttk/doc/dev/METAL_INITIALIZATION_IMPLEMENTATION.md  # TTK developer documentation
doc/REMOTE_LOG_MONITORING_FEATURE.md        # TFM end-user feature documentation
doc/dev/LOG_MANAGER_SYSTEM.md               # TFM developer system documentation
demo/demo_remote_log.py                     # Demo script
tools/log_analyzer.py                       # External tool
src/tfm_log_manager.py                      # Source code
temp/temp_refactoring_test.py               # Temporary test program
temp/TEMP_FEATURE_ANALYSIS.md               # Temporary documentation
```

#### Incorrect Placement (to be avoided)
```
remote_log_test.py                          # Should be in test/
doc/dev/METAL_BACKEND_IMPLEMENTATION.md     # TTK doc, should be in ttk/doc/dev/
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

## Documentation Quality Standards

### Content Separation Requirements

#### End-User Documentation Must NOT Include:
- Implementation details or code architecture
- Technical API references or code examples
- Internal system design explanations
- Developer-specific troubleshooting
- Performance implementation details
- Testing procedures or technical specifications

#### Developer Documentation Must NOT Include:
- Basic usage instructions for end users
- Simple configuration examples
- User-level troubleshooting steps
- Marketing-style feature benefits
- Non-technical feature descriptions

### Review Checklist

When reviewing documentation changes:
- [ ] Is the content appropriate for the target audience?
- [ ] Are implementation details separated from user instructions?
- [ ] Do both documents exist when user-facing changes are made?
- [ ] Are cross-references between documents appropriate and helpful?
- [ ] Is the naming convention followed correctly?
- [ ] Does the content follow the established patterns?

## Benefits of This Structure

- **Clear organization** - Easy to find files by purpose
- **Audience-focused content** - Users and developers get exactly what they need
- **Scalable** - Structure supports project growth
- **Standard conventions** - Follows Python project best practices
- **Tool-friendly** - IDEs and build tools work better with organized structure
- **Maintainable** - Easier to maintain and navigate the codebase
- **Reduced confusion** - No mixing of user and developer concerns
- **Better onboarding** - New users and developers can find relevant information quickly