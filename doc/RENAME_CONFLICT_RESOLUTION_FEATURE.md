# Rename Conflict Resolution Feature

## Overview

TFM now provides a "Rename" option when file conflicts occur during copy, move, and archive extraction operations. This allows users to specify a different destination filename instead of being limited to overwriting or skipping conflicting files.

## Feature Description

When a file operation encounters a naming conflict in the destination directory, users are presented with multiple resolution options:

- **Overwrite**: Replace the existing file with the new one
- **Skip**: Skip the conflicting file and continue with other files
- **Rename**: Specify a different name for the destination file
- **Cancel**: Abort the entire operation

## How It Works

### Copy Operations

When copying files to a destination where a file with the same name already exists:

1. TFM detects the conflict and shows a dialog with resolution options
2. If you select "Rename", an input dialog appears with the original filename
3. Edit the filename to your desired name
4. TFM checks if the new name also conflicts
5. If the new name conflicts, the dialog appears again with options to overwrite, rename again, or cancel
6. If the new name is available, the file is copied with the new name

### Move Operations

The rename process for move operations works identically to copy operations:

1. Conflict detected → dialog with options
2. Select "Rename" → input dialog appears
3. Enter new name → conflict check
4. Recursive conflict resolution if needed
5. File moved with new name when available

### Archive Extraction

When extracting an archive to a directory where the extraction folder already exists:

1. TFM detects that the target directory exists
2. Shows a dialog with "Overwrite", "Rename", or "Cancel" options
3. If you select "Rename", you can specify a different directory name
4. TFM checks if the new directory name conflicts
5. Recursive conflict resolution if needed
6. Archive extracted to the new directory name

**Note**: Archive extraction only has a single conflict (the target directory name), unlike copy/move operations which may have multiple file conflicts. Therefore, batch processing is not applicable to archive extraction.

## Usage Examples

### Example 1: Copy with Rename

```
Source: /home/user/documents/report.pdf
Destination: /home/user/backup/report.pdf (already exists)

1. Press F5 to copy
2. Dialog appears: "report.pdf already exists in destination"
3. Press 'r' for Rename
4. Input dialog shows: "Rename 'report.pdf' to:"
5. Edit to: "report_2024.pdf"
6. File copied as "report_2024.pdf"
```

### Example 2: Move with Recursive Rename

```
Source: /home/user/temp/data.csv
Destination: /home/user/archive/data.csv (already exists)

1. Press F6 to move
2. Dialog appears: "data.csv already exists in destination"
3. Press 'r' for Rename
4. Input dialog shows: "Rename 'data.csv' to:"
5. Edit to: "data_backup.csv"
6. Conflict check: "data_backup.csv" also exists
7. Dialog appears again: "data_backup.csv already exists in destination"
8. Press 'r' for Rename again
9. Edit to: "data_final.csv"
10. File moved as "data_final.csv"
```

### Example 3: Archive Extraction with Rename

```
Archive: /home/user/downloads/project.zip
Extraction target: /home/user/projects/project/ (already exists)

1. Press 'u' to extract
2. Dialog appears: "Directory 'project' already exists"
3. Press 'r' for Rename
4. Input dialog shows: "Rename extraction directory to:"
5. Edit to: "project_v2"
6. Archive extracted to "project_v2" directory
```

## Key Bindings

When the conflict resolution dialog appears:

- **o** - Overwrite existing file/directory
- **s** - Skip conflicting files (copy/move only)
- **r** - Rename to a different name
- **c** - Cancel the operation

## Batch Conflict Resolution

When multiple files have conflicts, selecting "Rename" will process each conflict one by one:

1. **First Conflict**: Dialog appears for the first conflicting file
   - Options: Overwrite, Rename, Skip, Skip All, Cancel
2. **Individual Decisions**: For each file, you can:
   - **Overwrite**: Replace this file and continue to next
   - **Rename**: Enter a new name for this file
   - **Skip**: Skip this file and continue to next
   - **Skip All**: Skip all remaining conflicts
   - **Cancel**: Abort the entire operation
3. **Automatic Processing**: Non-conflicting files are copied/moved automatically after all conflicts are resolved

### Example: Batch Rename Workflow

```
Files to copy: file1.txt, file2.txt, file3.txt, file4.txt
Conflicts: file1.txt, file2.txt, file3.txt
No conflict: file4.txt

1. Dialog for file1.txt → User selects "Rename" → Enters "file1_backup.txt"
2. Dialog for file2.txt → User selects "Overwrite"
3. Dialog for file3.txt → User selects "Skip"
4. file4.txt is copied automatically

Result:
- file1_backup.txt created (renamed)
- file2.txt overwritten
- file3.txt skipped (original preserved)
- file4.txt copied
```

## Limitations

- No automatic numbering (file_1.txt, file_2.txt)
- No pattern-based batch renaming
- Each conflict requires individual attention (but Skip All is available)

## Benefits

1. **Preserve Both Files**: Keep both the original and new file by renaming
2. **Avoid Accidental Overwrites**: Safer alternative to overwriting important files
3. **Flexible Naming**: Choose meaningful names during the operation
4. **Recursive Conflict Resolution**: Handles cases where the new name also conflicts
5. **Works Across Storage Types**: Supports local, S3, and other storage backends

## Technical Details

### Conflict Detection

TFM checks for conflicts by:
1. Comparing destination path with existing files
2. Using `Path.exists()` to verify file/directory existence
3. Recursively checking each renamed attempt

### Recursive Resolution

If the renamed file also conflicts:
1. The conflict dialog appears again
2. User can choose to overwrite, rename again, or cancel
3. Process continues until a unique name is found or user cancels

### Cross-Storage Support

The rename feature works across different storage types:
- Local filesystem to local filesystem
- Local to S3
- S3 to local
- S3 to S3

## Configuration

No additional configuration is required. The rename feature is automatically available when:
- `CONFIRM_COPY = True` (for copy operations)
- `CONFIRM_MOVE = True` (for move operations)
- `CONFIRM_EXTRACT_ARCHIVE = True` (for extraction operations)

These settings are enabled by default in `src/_config.py`.

## See Also

- [File Operations](FILE_OPERATIONS_FEATURE.md) - General file operation features
- [Archive Operations](ARCHIVE_OPERATIONS_FEATURE.md) - Archive creation and extraction
- [User Guide](TFM_USER_GUIDE.md) - Complete TFM user guide
