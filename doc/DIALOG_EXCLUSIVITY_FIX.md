# Dialog Exclusivity Fix

## Problem

When the help dialog was open, users could accidentally press search keys (like 'f') and start incremental search mode, creating a conflict where both the help dialog and search mode were active simultaneously.

## Root Cause

The input handling order in TFM was:

1. Handle search mode input
2. Handle dialog mode input  
3. Handle info dialog mode input
4. **Process regular key bindings** ← Problem here

When the help dialog was open (step 3), if it didn't handle a key, the regular key processing (step 4) would still run, potentially starting conflicting modes like search.

## Solution

Added a dialog exclusivity check after all dialog input handling:

```python
# Handle info dialog mode input
if self.info_dialog_mode:
    if self.handle_info_dialog_input(key):
        continue  # Info dialog mode handled the key

# Skip regular key processing if any dialog is open
# This prevents conflicts like starting search mode while help dialog is open
if self.dialog_mode or self.info_dialog_mode:
    continue

# Regular key processing only happens if no dialogs are open
if self.is_key_for_action(key, 'quit'):
    # ... regular key handling
```

## How It Works

### New Input Handling Flow

1. **Search Mode Priority**: If search mode is active, it handles all input first
2. **Dialog Input Handling**: Each dialog type gets a chance to handle keys
3. **Dialog Exclusivity Gate**: If ANY dialog is open, skip regular key processing
4. **Regular Key Processing**: Only runs when no dialogs are active

### Specific Scenarios

#### Scenario 1: Help Dialog Open, Search Key Pressed
**Before Fix:**
```
1. Help dialog open (info_dialog_mode = True)
2. User presses 'f' (search key)
3. Info dialog handler doesn't handle 'f'
4. Regular key processing runs
5. 'f' triggers search mode
6. ❌ CONFLICT: Both help dialog and search active
```

**After Fix:**
```
1. Help dialog open (info_dialog_mode = True)
2. User presses 'f' (search key)  
3. Info dialog handler doesn't handle 'f'
4. ✅ Regular key processing SKIPPED (dialog open)
5. ✅ Search mode NOT started
6. ✅ Help dialog remains focused
```

#### Scenario 2: Normal Operation
**Both Before and After:**
```
1. No dialogs open
2. User presses 'f' (search key)
3. No dialog handlers active
4. Regular key processing runs
5. ✅ Search mode starts normally
```

## Benefits

### 1. Prevents Mode Conflicts
- Help dialog and search mode are mutually exclusive
- Quick choice dialogs and search mode are mutually exclusive
- Any dialog blocks conflicting mode activation

### 2. Predictable User Experience
- Dialogs maintain focus until explicitly closed
- No accidental mode switches
- Clear, consistent behavior

### 3. Clean Architecture
- Simple, understandable input flow
- Single point of control for dialog exclusivity
- Easy to maintain and extend

## Implementation Details

### Code Changes
- **File**: `tfm_main.py`
- **Location**: Main input handling loop (`run()` method)
- **Change**: Added dialog exclusivity check before regular key processing

### Lines Added
```python
# Skip regular key processing if any dialog is open
# This prevents conflicts like starting search mode while help dialog is open
if self.dialog_mode or self.info_dialog_mode:
    continue
```

### Affected Modes
- **Info Dialog Mode** (help dialog): Blocks all regular key processing
- **Dialog Mode** (quick choice dialogs): Blocks all regular key processing
- **Search Mode**: Maintains priority (handles input first)

## Testing

### Test Coverage
- ✅ Normal operation (no dialogs)
- ✅ Help dialog blocks search activation
- ✅ Quick choice dialog blocks search activation
- ✅ Search mode maintains priority
- ✅ Dialog handlers get first chance at keys
- ✅ Regular processing properly gated

### User Scenarios Tested
1. **Help dialog + accidental search key**: Search blocked ✅
2. **Search mode + help key**: Search handles it ✅
3. **File operations dialog + search key**: Search blocked ✅
4. **Normal search activation**: Works normally ✅

## Future Considerations

### Extensibility
The fix is designed to be extensible:
- New dialog types automatically get exclusivity
- Just add them to the exclusivity check
- Maintains clean separation of concerns

### Potential Enhancements
1. **Context-sensitive keys**: Allow some keys to work in dialog contexts
2. **Dialog stacking**: Support multiple dialog layers
3. **Mode transitions**: Smooth transitions between modes

## Conclusion

This fix ensures that TFM's dialog system works predictably and prevents user confusion from accidental mode conflicts. The help dialog now provides a focused, uninterrupted experience for users learning TFM's features.

### Key Outcomes
- ✅ Help dialog and search mode are mutually exclusive
- ✅ Clean, predictable user experience
- ✅ No accidental mode conflicts
- ✅ Maintainable, extensible architecture