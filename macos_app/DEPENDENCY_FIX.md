# Dependency Collection Fix

## Issue
The build script was collecting Python dependencies from the user's site-packages directory (`~/.local/lib/python3.12/site-packages`) instead of the project's virtual environment.

## Problem
This could lead to:
- Inconsistent dependency versions across different builds
- Including packages not listed in requirements.txt
- Missing packages that are only in the project's venv
- Build failures when user's Python environment differs from project requirements

## Solution
Updated `macos_app/collect_dependencies.py` to prioritize the project's virtual environment:

### Changes Made

1. **Updated `get_site_packages_dir()` function:**
   - Now searches for `.venv/lib/python3.12/site-packages` in current and parent directories
   - Prioritizes virtual environment paths in sys.path
   - Falls back to user site-packages only if venv not found
   - Logs which site-packages directory is being used

2. **Updated `get_package_dependencies()` function:**
   - Changed from `pip show` to `python3 -m pip show`
   - Uses `sys.executable` to ensure correct Python interpreter
   - Works correctly within virtual environments

## Verification

After the fix, the build script now correctly reports:
```
[INFO] Using project virtual environment: /Users/shimomut/projects/tfm/.venv/lib/python3.12/site-packages
```

Instead of:
```
[INFO] Using site-packages: /Users/shimomut/.local/lib/python3.12/site-packages
```

## Testing

To verify the fix works:

1. **Check which site-packages is used:**
   ```bash
   cd macos_app
   ./build.sh 2>&1 | grep "site-packages"
   ```
   Should show: `Using project virtual environment: .../tfm/.venv/lib/python3.12/site-packages`

2. **Verify dependencies are collected:**
   ```bash
   ls -la build/TFM.app/Contents/Resources/python_packages/
   ```
   Should show packages from requirements.txt (pygments, boto3, etc.)

3. **Test the app launches:**
   ```bash
   open build/TFM.app
   ```
   Should launch without import errors

## Impact

This fix ensures:
- ✅ Consistent builds across different developer machines
- ✅ Only dependencies from requirements.txt are included
- ✅ Correct package versions are bundled
- ✅ Better isolation from system Python packages
- ✅ More reliable builds in CI/CD environments

## Date
December 27, 2025
