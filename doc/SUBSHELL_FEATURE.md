# Sub-shell Mode Feature

## Overview

The sub-shell mode feature allows users to temporarily suspend the TFM interface and enter a shell environment with pre-configured environment variables that provide access to the current state of both file panes and selected files.

## Activation

- **Key binding**: `x` or `X`
- **Action**: Suspends TFM curses interface and starts a new shell session
- **Visual indicator**: Shell prompt includes `[TFM]` label for easy identification

## Environment Variables

When entering sub-shell mode, the following environment variables are automatically set:

### Directory Variables
- `LEFT_DIR`: Absolute path of the left file pane directory
- `RIGHT_DIR`: Absolute path of the right file pane directory  
- `THIS_DIR`: Absolute path of the currently focused pane directory
- `OTHER_DIR`: Absolute path of the non-focused pane directory

### Selected Files Variables
- `LEFT_SELECTED`: Space-separated list of selected file names in the left pane
- `RIGHT_SELECTED`: Space-separated list of selected file names in the right pane
- `THIS_SELECTED`: Space-separated list of selected file names in the focused pane
- `OTHER_SELECTED`: Space-separated list of selected file names in the non-focused pane

## Usage Examples

### Basic Directory Operations

```bash
# List files in both panes
ls -la "$LEFT_DIR" "$RIGHT_DIR"

# Compare directory sizes
du -sh "$LEFT_DIR" "$RIGHT_DIR"

# Find files in both directories
find "$LEFT_DIR" "$RIGHT_DIR" -name "*.py"
```

### Working with Selected Files

```bash
# Copy selected files from current pane to other pane
for file in $THIS_SELECTED; do
    cp "$THIS_DIR/$file" "$OTHER_DIR/"
done

# Show details of selected files
for file in $THIS_SELECTED; do
    ls -la "$THIS_DIR/$file"
done

# Archive selected files
if [ -n "$THIS_SELECTED" ]; then
    cd "$THIS_DIR"
    tar -czf selected_files.tar.gz $THIS_SELECTED
fi
```

### Advanced Operations

```bash
# Sync directories (copy newer files)
rsync -av "$THIS_DIR/" "$OTHER_DIR/"

# Compare selected files between panes
for file in $THIS_SELECTED; do
    if [ -f "$OTHER_DIR/$file" ]; then
        diff "$THIS_DIR/$file" "$OTHER_DIR/$file"
    fi
done

# Batch rename selected files
for file in $THIS_SELECTED; do
    mv "$THIS_DIR/$file" "$THIS_DIR/backup_$file"
done
```

## Shell Integration

The sub-shell mode uses the user's default shell (from `$SHELL` environment variable) or falls back to `/bin/bash`. This ensures compatibility with the user's preferred shell configuration, aliases, and functions.

## Working Directory

When entering sub-shell mode, the working directory is automatically changed to the currently focused pane's directory (`$THIS_DIR`).

## Shell Prompt Customization

TFM sets the `TFM_ACTIVE` environment variable when entering sub-shell mode. To display the `[TFM]` label in your shell prompt, you need to customize your shell configuration files.

### Why Manual Configuration is Needed

Shell configuration files (like `.zshrc` and `.bashrc`) are loaded after TFM sets environment variables, which overwrites any prompt modifications TFM makes. The solution is to modify your shell configuration to check for the `TFM_ACTIVE` environment variable and adjust the prompt accordingly.

### Zsh Configuration

Add this to your `~/.zshrc` file:

```bash
# TFM sub-shell prompt modification
if [[ -n "$TFM_ACTIVE" ]]; then
    PROMPT="[TFM] $PROMPT"
fi
```

### Bash Configuration

Add this to your `~/.bashrc` file:

```bash
# TFM sub-shell prompt modification
if [[ -n "$TFM_ACTIVE" ]]; then
    PS1="[TFM] $PS1"
fi
```

### Advanced Prompt Customization

For more sophisticated prompt modifications, you can create conditional logic:

#### Zsh Advanced Example
```bash
# Advanced TFM prompt customization for zsh
if [[ -n "$TFM_ACTIVE" ]]; then
    # Add colored [TFM] label
    PROMPT="%F{yellow}[TFM]%f $PROMPT"
    
    # Or modify the right prompt
    RPROMPT="$RPROMPT %F{red}(TFM)%f"
fi
```

#### Bash Advanced Example
```bash
# Advanced TFM prompt customization for bash
if [[ -n "$TFM_ACTIVE" ]]; then
    # Add colored [TFM] label
    PS1="\[\033[1;33m\][TFM]\[\033[0m\] $PS1"
    
    # Or create a completely custom TFM prompt
    PS1="\[\033[1;33m\][TFM]\[\033[0m\] \[\033[1;32m\]\u@\h\[\033[0m\]:\[\033[1;34m\]\w\[\033[0m\]\$ "
fi
```

### Testing Your Configuration

1. **Add the configuration** to your shell config file (`.zshrc` or `.bashrc`)
2. **Reload your shell configuration**:
   ```bash
   # For zsh
   source ~/.zshrc
   
   # For bash  
   source ~/.bashrc
   ```
3. **Test manually** (optional):
   ```bash
   # Set the variable and start a new shell to test
   TFM_ACTIVE=1 zsh  # or bash
   # You should see [TFM] in the prompt
   exit
   ```
4. **Test with TFM**:
   - Start TFM and press `x` to enter sub-shell mode
   - Your prompt should now display the `[TFM]` label
   - Type `exit` to return to TFM

### Environment Variable Details

When `TFM_ACTIVE` is set:
- **Value**: Always set to `"1"`
- **Scope**: Only available in the TFM sub-shell session
- **Persistence**: Automatically unset when exiting the sub-shell

### Shell Compatibility

| Shell | Config File | Variable | Example |
|-------|-------------|----------|---------|
| zsh | `~/.zshrc` | `PROMPT` | `[TFM] %n@%m:%~%# ` |
| bash | `~/.bashrc` | `PS1` | `[TFM] \u@\h:\w\$ ` |
| fish | `~/.config/fish/config.fish` | Custom function | See fish documentation |

### Troubleshooting

**Prompt not showing [TFM] label:**
1. Verify the configuration is added to the correct file
2. Make sure the syntax is correct for your shell
3. Test by manually setting `TFM_ACTIVE=1` and starting a new shell
4. Check if other prompt modifications in your config are overriding the TFM setting

**Configuration conflicts:**
- Place the TFM configuration **after** other prompt modifications in your config file
- Some prompt themes may override the `PROMPT` or `PS1` variables - adjust accordingly

## Returning to TFM

To return to TFM from sub-shell mode:
- Type `exit` in the shell
- Press `Ctrl+D` (EOF)
- The TFM interface will be restored automatically

## Error Handling

- If the shell fails to start, an error message is displayed
- The curses interface is properly restored even if errors occur
- Log messages are captured when returning to TFM

## Configuration

The sub-shell feature can be customized through the key bindings configuration:

```python
KEY_BINDINGS = {
    'subshell': ['x', 'X'],  # Customize the key binding
    # ... other bindings
}
```

## Implementation Details

### Curses Management
- The curses interface is properly suspended using `curses.endwin()`
- Terminal is restored to normal mode for shell interaction
- Curses is reinitialized when returning to TFM

### Environment Preservation
- Original stdout/stderr are temporarily restored
- Log capture is suspended during shell session
- All TFM state is preserved and restored
- Environment variables are properly passed using `subprocess.run()`

### Path Handling
- All paths are converted to absolute paths for reliability
- Path expansion and resolution is handled automatically
- Non-existent or inaccessible paths are handled gracefully

### Shell Integration
- Uses `subprocess.run()` with explicit environment passing
- Supports user's preferred shell from `$SHELL` environment variable
- Falls back to `/bin/bash` if `$SHELL` is not set
- Modifies both `PS1` and `PROMPT` environment variables for broad shell compatibility
- Preserves existing prompt customizations while adding TFM identification
- Works with bash, zsh, sh, dash, and other POSIX-compatible shells

## Use Cases

1. **Batch Operations**: Perform complex operations on selected files using shell tools
2. **System Integration**: Use system commands with TFM's file selection
3. **Scripting**: Write and execute scripts that operate on TFM's current state
4. **Advanced File Management**: Use specialized tools like `rsync`, `find`, `grep`, etc.
5. **Development Workflow**: Integrate TFM with development tools and build systems

## Testing

Use the provided test scripts to verify functionality:

```bash
# Test environment variables
python3 test_subshell.py

# See usage examples
python3 demo_subshell.py
```

## Security Considerations

- Environment variables contain file paths and names from TFM
- Selected file names are passed as space-separated strings
- Users should be cautious with file names containing special characters
- Standard shell quoting and escaping practices apply