# Natural Sorting Feature

## Overview

TFM uses natural sorting (also called alphanumeric sorting) when sorting files and directories by name. This means numeric sequences within filenames are treated as numbers rather than strings, resulting in more intuitive ordering.

## How It Works

### Dictionary vs Natural Sorting

**Dictionary sorting** (old behavior):
```
Test1.txt
Test10.txt
Test100.txt
Test11.txt
Test2.txt
Test3.txt
```

**Natural sorting** (current behavior):
```
Test1.txt
Test2.txt
Test3.txt
Test10.txt
Test11.txt
Test100.txt
```

### Key Features

- **Numeric sequences are sorted numerically**: "file2.txt" comes before "file10.txt"
- **Case-insensitive**: "Test1.txt" and "test1.txt" are treated the same
- **Multiple numeric parts**: "file1-part10.txt" sorts correctly after "file1-part2.txt"
- **Leading zeros**: "Report001.pdf" sorts before "Report010.pdf"
- **Directories and files**: Both are sorted naturally within their respective groups

## Examples

### Simple Numeric Sequences

Files with simple numeric sequences sort intuitively:
```
Chapter1.md
Chapter2.md
Chapter10.md
Chapter20.md
```

### Complex Filenames

Files with multiple numeric parts:
```
file1-part2.txt
file1-part10.txt
file2-part1.txt
```

### Leading Zeros

Files with leading zeros maintain proper order:
```
Report001.pdf
Report002.pdf
Report010.pdf
Report100.pdf
```

### Mixed Content

Natural sorting works with any combination of text and numbers:
```
Image1.jpg
Image5.jpg
Image10.jpg
Image50.jpg
Image100.jpg
```

## Usage

Natural sorting is automatically applied when:
- Sorting by **Name** (default sort mode)
- Browsing directories
- Navigating file lists

To sort by name:
1. Press `s` to open the sort menu
2. Select "Name" (or press `n`)

Natural sorting is always active for name-based sorting and cannot be disabled.

## Benefits

- **More intuitive**: Files appear in the order you expect
- **Better for numbered sequences**: Perfect for chapters, versions, reports, etc.
- **Consistent**: Works the same way across all file types
- **Standard behavior**: Matches how most modern file managers sort files

## Technical Notes

- Natural sorting only applies to name-based sorting
- Other sort modes (size, date, extension) are unaffected
- Directories are always listed before files, regardless of sort mode
- The sorting is stable and deterministic
