---
inclusion: always
---

# Test File Placement Rules

## Test File Location
- ALL test files must be created in the `/test` directory
- Test files should follow the naming convention `test_*.py`
- Never create test files in the root directory or `/src` directory
- When creating new tests, always use the path `test/test_<feature_name>.py`

## Test File Structure
- Each test file should be self-contained
- Include proper imports with `sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))`
- Follow the existing test patterns in the codebase

## Examples
- Feature tests: `test/test_feature_name.py`
- Integration tests: `test/test_integration_*.py`
- Unit tests: `test/test_unit_*.py`