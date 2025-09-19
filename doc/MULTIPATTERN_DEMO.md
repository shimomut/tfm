# TFM Multi-Pattern Search Demo

## How Multi-Pattern Search Works

TFM's incremental search now supports multiple space-delimited patterns where **ALL patterns must match** the filename.

### Pattern Processing

1. **Input**: `ab*c 12?3`
2. **Split by spaces**: `["ab*c", "12?3"]`
3. **Wrap with wildcards**: `["*ab*c*", "*12?3*"]`
4. **Match requirement**: Filename must match BOTH patterns

### Real Examples

#### Example 1: Finding Test Configuration Files
**Search**: `test config`
- **Processed as**: `*test*` AND `*config*`
- **Matches**: 
  - ✅ `test_config.py`
  - ✅ `config_test.txt`
  - ✅ `app_config_test.js`
  - ❌ `test_file.py` (no "config")
  - ❌ `config.json` (no "test")

#### Example 2: Python Test Files
**Search**: `*.py test`
- **Processed as**: `*.py*` AND `*test*`
- **Matches**:
  - ✅ `test_main.py`
  - ✅ `my_test.py`
  - ✅ `unittest_helper.py`
  - ❌ `test_file.txt` (not .py)
  - ❌ `main.py` (no "test")

#### Example 3: Complex Pattern Matching
**Search**: `ab*c 12?3`
- **Processed as**: `*ab*c*` AND `*12?3*`
- **Matches**:
  - ✅ `abc_1203_file.txt` (matches ab*c and 12?3)
  - ✅ `my_abc_data_1243.log` (matches ab*c and 12?3)
  - ❌ `abc_file.txt` (no 12?3 pattern)
  - ❌ `data_1203.txt` (no ab*c pattern)

### Usage Tips

1. **Start Simple**: Begin with one pattern, add more as needed
2. **Use Wildcards**: Combine exact patterns with wildcards (`*.py test`)
3. **Case Insensitive**: `TEST Config` matches `test_config.py`
4. **Real-time Feedback**: See matches update as you type each pattern
5. **Space Separation**: Use spaces to separate different search criteria

### Interactive Demo

Try these patterns in TFM:

```
# Find Python files containing "test"
*.py test

# Find configuration files with "app" in the name
config app

# Find files with both "main" and a 3-digit number
main ???

# Find JavaScript/TypeScript files containing "component"
*.js component
*.ts component

# Find files containing "user", "auth", and ending in .json
user auth *.json
```

### Benefits

- **Precise Filtering**: Narrow down results with multiple criteria
- **Flexible Patterns**: Mix exact text with wildcards
- **Intuitive Syntax**: Natural space-separated search terms
- **Real-time Results**: Immediate feedback as you type
- **Powerful Combinations**: Combine file extensions, names, and content patterns