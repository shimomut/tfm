# Search Dialog Component

## Overview

The Search Dialog Component provides comprehensive search functionality for TFM, enabling users to search for files by name patterns and content using grep-like functionality. It offers both filename search and content search with real-time results and easy navigation.

## Features

### Core Capabilities
- **Filename Search**: Search for files by name patterns with wildcards
- **Content Search**: Search within file contents using grep functionality
- **Real-time Results**: Live search results as you type
- **Pattern Matching**: Support for wildcards and regular expressions
- **Result Navigation**: Easy navigation to search results

### Advanced Features
- **Incremental Search**: Updates results as search pattern changes
- **Case Sensitivity Options**: Toggle case-sensitive search
- **Multiple Search Types**: Different search modes for different needs
- **Result Highlighting**: Visual highlighting of search terms
- **Quick Navigation**: Direct navigation to found files

## Class Structure

### SearchDialog Class
```python
class SearchDialog:
    def __init__(self, config)
    def show_filename_search(self, initial_pattern="")
    def show_content_search(self, initial_pattern="")
    def handle_input(self, key)
    def draw(self, stdscr, safe_addstr_func)
    def exit()
```

### Search Result Structure
```python
search_result = {
    'file_path': Path,      # Path to the found file
    'match_type': str,      # Type of match (filename/content)
    'line_number': int,     # Line number for content matches
    'match_text': str,      # Matching text or context
    'highlight_start': int, # Start position of highlight
    'highlight_end': int    # End position of highlight
}
```

## Usage Examples

### Filename Search
```python
search_dialog = SearchDialog(config)

# Show filename search dialog
search_dialog.show_filename_search(initial_pattern="*.py")

# Handle results in callback
def handle_filename_result(result):
    navigate_to_file(result['file_path'])

search_dialog.set_result_callback(handle_filename_result)
```

### Content Search
```python
# Show content search dialog
search_dialog.show_content_search(initial_pattern="function")

# Handle content search results
def handle_content_result(result):
    open_file_at_line(result['file_path'], result['line_number'])

search_dialog.set_result_callback(handle_content_result)
```

### Advanced Pattern Search
```python
# Search with regular expression
search_dialog.show_content_search(initial_pattern="def\\s+\\w+\\(")

# Search with case sensitivity
search_dialog.set_case_sensitive(True)
search_dialog.show_filename_search("README*")
```

## Search Types

### Filename Search
- **Wildcard Patterns**: Use `*` and `?` for pattern matching
- **Case Sensitivity**: Optional case-sensitive filename matching
- **Extension Filtering**: Search by file extensions
- **Path Matching**: Match against full file paths

#### Filename Search Examples
```
Pattern: "*.py"          → Finds all Python files
Pattern: "test_*"        → Finds files starting with "test_"
Pattern: "*config*"      → Finds files containing "config"
Pattern: "README.??"     → Finds README.md, README.txt, etc.
```

### Content Search (Grep)
- **Text Patterns**: Search for text within file contents
- **Regular Expressions**: Full regex support for complex patterns
- **Line Context**: Shows matching lines with context
- **Multiple Files**: Searches across multiple files simultaneously

#### Content Search Examples
```
Pattern: "function"      → Finds lines containing "function"
Pattern: "def \\w+"      → Finds function definitions (regex)
Pattern: "TODO|FIXME"    → Finds TODO or FIXME comments
Pattern: "import .*"     → Finds import statements
```

## Visual Design

### Search Dialog Layout
```
┌─────────────────────────────────────────────────────────────┐
│ Search Files                                                │
├─────────────────────────────────────────────────────────────┤
│ Pattern: *.py                                               │
├─────────────────────────────────────────────────────────────┤
│ Results (15 found):                                         │
│ > src/tfm_main.py                                          │
│   src/tfm_config.py                                        │
│   src/tfm_colors.py                                        │
│   test/test_main.py                                         │
│   test/test_config.py                                       │
│   ...                                                       │
├─────────────────────────────────────────────────────────────┤
│ ↑↓=Navigate Enter=Open ESC=Cancel                          │
└─────────────────────────────────────────────────────────────┘
```

### Content Search Layout
```
┌─────────────────────────────────────────────────────────────┐
│ Search Content                                              │
├─────────────────────────────────────────────────────────────┤
│ Pattern: function                                           │
├─────────────────────────────────────────────────────────────┤
│ Results (8 matches in 3 files):                            │
│ > main.py:15: def main_function():                         │
│   main.py:42:     helper_function(args)                    │
│   utils.py:8: def utility_function(data):                  │
│   utils.py:23:     return process_function(data)           │
│   ...                                                       │
├─────────────────────────────────────────────────────────────┤
│ ↑↓=Navigate Enter=Open ESC=Cancel                          │
└─────────────────────────────────────────────────────────────┘
```

## Navigation Controls

### Keyboard Shortcuts
- **↑/↓ Arrow Keys**: Navigate through search results
- **Page Up/Page Down**: Navigate by pages through results
- **Home/End**: Jump to first/last result
- **Enter**: Open selected file or navigate to match
- **ESC**: Cancel search and close dialog
- **F3**: Toggle case sensitivity (if supported)

### Search Pattern Controls
- **Type Characters**: Build search pattern
- **Backspace**: Remove characters from pattern
- **Delete**: Clear entire search pattern
- **Tab**: Switch between search modes (if applicable)

## Helper Functions

### SearchDialogHelpers Class
Utility functions for search dialog integration:

#### Navigate to Result
```python
SearchDialogHelpers.navigate_to_result(result, pane_manager, file_operations, print_func)
```
Navigates to the selected search result, opening files or changing directories as appropriate.

#### Format Search Results
```python
formatted_results = SearchDialogHelpers.format_search_results(raw_results, search_type)
```
Formats raw search results for display in the dialog.

#### Execute Search
```python
results = SearchDialogHelpers.execute_filename_search(pattern, search_path)
results = SearchDialogHelpers.execute_content_search(pattern, search_path, case_sensitive)
```
Executes the actual search operations and returns formatted results.

## Integration with TFM

### Main Application Integration
```python
# In FileManager class
self.search_dialog = SearchDialog(self.config)

# Show filename search
def show_filename_search(self):
    self.search_dialog.show_filename_search()

# Show content search
def show_content_search(self):
    self.search_dialog.show_content_search()

# Handle input in main loop
if self.search_dialog.mode:
    if self.search_dialog.handle_input(key):
        self.needs_full_redraw = True
    return True  # Input consumed
```

### Drawing Integration
```python
# In main draw loop
if self.search_dialog.mode:
    self.search_dialog.draw(self.stdscr, self.safe_addstr)
```

## Search Implementation

### Filename Search Algorithm
```python
def execute_filename_search(self, pattern, search_path):
    """Execute filename search with pattern matching"""
    results = []
    
    # Convert wildcard pattern to regex
    regex_pattern = self.wildcard_to_regex(pattern)
    compiled_pattern = re.compile(regex_pattern, re.IGNORECASE if not self.case_sensitive else 0)
    
    # Search through directory tree
    for file_path in search_path.rglob('*'):
        if file_path.is_file():
            if compiled_pattern.search(file_path.name):
                results.append({
                    'file_path': file_path,
                    'match_type': 'filename',
                    'match_text': file_path.name
                })
    
    return results
```

### Content Search Algorithm
```python
def execute_content_search(self, pattern, search_path):
    """Execute content search using grep-like functionality"""
    results = []
    
    # Compile search pattern
    flags = re.IGNORECASE if not self.case_sensitive else 0
    compiled_pattern = re.compile(pattern, flags)
    
    # Search through files
    for file_path in search_path.rglob('*'):
        if file_path.is_file() and self.is_text_file(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        match = compiled_pattern.search(line)
                        if match:
                            results.append({
                                'file_path': file_path,
                                'match_type': 'content',
                                'line_number': line_num,
                                'match_text': line.strip(),
                                'highlight_start': match.start(),
                                'highlight_end': match.end()
                            })
            except Exception:
                # Skip files that can't be read
                continue
    
    return results
```

## Performance Optimization

### Efficient Search
- **Incremental Updates**: Only research when pattern changes significantly
- **File Type Filtering**: Skip binary files for content search
- **Result Limiting**: Limit number of results to prevent UI flooding
- **Background Search**: Non-blocking search execution
- **Caching**: Cache recent search results for quick access

### Search Optimization
```python
class SearchDialog:
    def __init__(self, config):
        self.search_cache = {}
        self.max_results = 1000
        self.search_timeout = 5.0  # 5 second timeout
    
    def optimized_search(self, pattern, search_type):
        """Perform optimized search with caching and limits"""
        cache_key = (pattern, search_type, self.case_sensitive)
        
        # Check cache first
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]
        
        # Perform search with timeout
        results = self.execute_search_with_timeout(pattern, search_type)
        
        # Limit results
        if len(results) > self.max_results:
            results = results[:self.max_results]
        
        # Cache results
        self.search_cache[cache_key] = results
        
        return results
```

## Advanced Features

### Search Options
```python
class SearchOptions:
    def __init__(self):
        self.case_sensitive = False
        self.include_hidden = False
        self.file_types = None  # None = all files
        self.max_results = 1000
        self.search_subdirs = True
```

### Custom File Filters
```python
def set_file_type_filter(self, file_types):
    """Set file type filter for search"""
    self.file_type_filter = file_types
    
def is_searchable_file(self, file_path):
    """Check if file should be included in search"""
    if self.file_type_filter:
        return file_path.suffix.lower() in self.file_type_filter
    return True
```

### Search History
```python
class SearchDialog:
    def __init__(self, config):
        self.search_history = []
        self.max_history = 50
    
    def add_to_history(self, pattern, search_type):
        """Add search pattern to history"""
        entry = (pattern, search_type, time.time())
        self.search_history.insert(0, entry)
        
        # Limit history size
        if len(self.search_history) > self.max_history:
            self.search_history = self.search_history[:self.max_history]
```

## Error Handling

### Search Errors
- **Invalid Patterns**: Handle malformed regex patterns gracefully
- **Permission Errors**: Skip files/directories without read permission
- **File Encoding**: Handle files with different encodings safely
- **Large Files**: Handle very large files without blocking UI
- **Network Issues**: Handle network path search problems

### Recovery Mechanisms
```python
def safe_search(self, pattern, search_path):
    """Perform search with comprehensive error handling"""
    try:
        return self.execute_search(pattern, search_path)
    except re.error as e:
        self.show_error(f"Invalid search pattern: {e}")
        return []
    except PermissionError:
        self.show_error("Permission denied accessing some files")
        return []
    except Exception as e:
        self.show_error(f"Search error: {e}")
        return []
```

## Common Use Cases

### Find Configuration Files
```python
# Search for config files
search_dialog.show_filename_search("*config*")
search_dialog.show_filename_search("*.conf")
search_dialog.show_filename_search("*.ini")
```

### Find Source Code
```python
# Search for Python files
search_dialog.show_filename_search("*.py")

# Search for function definitions
search_dialog.show_content_search("def \\w+\\(")

# Search for TODO comments
search_dialog.show_content_search("TODO|FIXME")
```

### Find Documentation
```python
# Search for documentation files
search_dialog.show_filename_search("README*")
search_dialog.show_filename_search("*.md")

# Search for specific documentation content
search_dialog.show_content_search("installation|setup")
```

## Benefits

### User Experience
- **Quick File Finding**: Rapidly locate files by name or content
- **Real-time Results**: Immediate feedback as you type
- **Easy Navigation**: Simple keyboard navigation to results
- **Comprehensive Search**: Both filename and content search capabilities

### Developer Experience
- **Simple API**: Easy to integrate search functionality
- **Flexible Configuration**: Customizable search options and behavior
- **Helper Functions**: Pre-built functions for common search tasks
- **Performance Optimized**: Efficient search algorithms and caching

### Productivity
- **Fast File Location**: Quickly find files in large directory trees
- **Content Discovery**: Find files containing specific text or patterns
- **Workflow Integration**: Seamless integration with file management tasks
- **Search History**: Remember and reuse previous searches

## Future Enhancements

### Potential Improvements
- **Fuzzy Search**: Approximate string matching for typos
- **Search Filters**: Filter results by file type, size, date
- **Search Bookmarks**: Save and recall frequent search patterns
- **Multi-Pattern Search**: Search for multiple patterns simultaneously
- **Search Replace**: Find and replace functionality

### Advanced Features
- **Index-Based Search**: Pre-built search indexes for faster results
- **Network Search**: Search across network locations
- **Plugin Search**: Extensible search plugins for different file types
- **Visual Search**: GUI-based search pattern builder
- **Search Analytics**: Track and analyze search patterns

## Testing

### Test Coverage
- **Pattern Matching**: Verify correct pattern matching algorithms
- **Search Results**: Test result accuracy and formatting
- **Navigation**: Test result navigation and selection
- **Error Handling**: Test error conditions and recovery
- **Performance**: Test search performance with large datasets

### Test Scenarios
- **Basic Searches**: Simple filename and content searches
- **Complex Patterns**: Regular expressions and wildcard patterns
- **Edge Cases**: Empty patterns, no results, large result sets
- **Error Conditions**: Invalid patterns, permission errors
- **Performance**: Large directory trees and many files

## Conclusion

The Search Dialog Component provides powerful, efficient search capabilities for TFM, enabling users to quickly locate files by name or content. Its combination of real-time results, flexible pattern matching, and easy navigation makes it an essential tool for effective file management and code exploration.