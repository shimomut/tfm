<#
.SYNOPSIS
    Build the self-contained TFM Windows application bundle.

.DESCRIPTION
    Windows counterpart of macos_app/build.sh. Assembles build\TFM\ containing a
    compiled C launcher (TFM.exe), an embedded CPython (from the python.org
    "embeddable" package matching the .venv's version), TFM's own code, PuiKit,
    and all third-party dependencies. See doc/dev/WINDOWS_APP_BUILD_SYSTEM.md.

.PARAMETER Version
    Version string embedded in TFM.exe (e.g. 1.0.0). Defaults to tfm.py's _VERSION.

.PARAMETER PythonEmbedUrl
    Override the embeddable-package download URL (default: python.org, matching
    the venv's exact version).

.PARAMETER Zip
    Also produce build\TFM-<version>-win64.zip for distribution.

.PARAMETER Clean
    Remove the build directory and exit.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File windows_app\build.ps1
    powershell -ExecutionPolicy Bypass -File windows_app\build.ps1 -Version 1.0.0 -Zip
#>
[CmdletBinding()]
param(
    [string]$Version,
    [string]$PythonEmbedUrl,
    [switch]$Zip,
    [switch]$Clean
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
$ScriptDir   = $PSScriptRoot
$ProjectRoot = Split-Path -Parent $ScriptDir
$SrcDir      = Join-Path $ScriptDir 'src'
$ResDir      = Join-Path $ScriptDir 'resources'
$BuildDir    = Join-Path $ScriptDir 'build'
$AppRoot     = Join-Path $BuildDir 'TFM'      # the distributable folder
$ObjDir      = Join-Path $BuildDir 'obj'      # launcher intermediates
$CacheDir    = Join-Path $ScriptDir '.cache'  # downloaded embeddable zips

$AppName = 'TFM'

function Info    ($m) { Write-Host "[INFO] $m" }
function Success ($m) { Write-Host "[SUCCESS] $m" -ForegroundColor Green }
function Warn    ($m) { Write-Host "[WARNING] $m" -ForegroundColor Yellow }
function Fail    ($m) { Write-Host "[ERROR] $m" -ForegroundColor Red; exit 1 }

if ($Clean) {
    if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir; Info "Removed $BuildDir" }
    else { Info "Nothing to clean." }
    return
}

# ---------------------------------------------------------------------------
# Step 1: Locate the build virtual environment and derive Python facts
# ---------------------------------------------------------------------------
Info 'Step 1: Inspecting the build virtual environment...'

$VenvPy = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $VenvPy)) {
    Fail ".venv not found at $VenvPy. Run 'make venv' first."
}

# One round-trip that prints the facts we need, tab-separated.
$probe = & $VenvPy -c @"
import sys, sysconfig, platform
print('\t'.join([
    platform.python_version(),                                   # 3.14.6
    '%d.%d' % sys.version_info[:2],                              # 3.14
    '%d%d' % sys.version_info[:2],                               # 314
    sys.base_prefix,                                             # full-CPython root
    sysconfig.get_paths()['purelib'],                           # venv site-packages
]))
"@
if ($LASTEXITCODE -ne 0) { Fail 'Failed to probe the venv interpreter.' }
$parts       = $probe.Trim() -split "`t"
$PyFull      = $parts[0]
$PyXY        = $parts[1]
$PyNoDot     = $parts[2]
$BasePrefix  = $parts[3]
$SitePkgs    = $parts[4]

$PyInclude = Join-Path $BasePrefix 'include'
$PyLibs    = Join-Path $BasePrefix 'libs'

Info "Python:        $PyFull (ABI cp$PyNoDot)"
Info "base_prefix:   $BasePrefix"
Info "site-packages: $SitePkgs"

if (-not (Test-Path (Join-Path $PyInclude 'Python.h'))) {
    Fail "Python.h not found under $PyInclude. The .venv must be backed by a full CPython install (headers + libs), which 'make venv' provides."
}
if (-not (Test-Path (Join-Path $PyLibs "python$PyNoDot.lib"))) {
    Fail "python$PyNoDot.lib not found under $PyLibs."
}

# Resolve the version string to embed.
if (-not $Version) {
    $tfmPy = Join-Path $ProjectRoot 'tfm.py'
    $m = Select-String -Path $tfmPy -Pattern '_VERSION\s*=\s*"([^"]+)"' | Select-Object -First 1
    if ($m) { $Version = $m.Matches[0].Groups[1].Value } else { $Version = '0.0.0' }
}
Info "Bundle version: $Version"

# ---------------------------------------------------------------------------
# Step 2: Locate the C toolchain (cl.exe + rc.exe), importing VS env if needed
# ---------------------------------------------------------------------------
Info 'Step 2: Locating the MSVC toolchain...'

function Import-VsDevEnv {
    $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    if (-not (Test-Path $vswhere)) { return $false }
    $vsPath = & $vswhere -latest -products * `
        -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
        -property installationPath
    if (-not $vsPath) { return $false }
    $devCmd = Join-Path $vsPath 'Common7\Tools\VsDevCmd.bat'
    if (-not (Test-Path $devCmd)) { return $false }
    Info "Importing environment from $devCmd"
    cmd /c "`"$devCmd`" -arch=amd64 -host_arch=amd64 && set" | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
        }
    }
    return $true
}

if (-not (Get-Command cl.exe -ErrorAction SilentlyContinue)) {
    if (-not (Import-VsDevEnv)) {
        Fail @"
MSVC toolchain (cl.exe) not found.

Install the 'Build Tools for Visual Studio' with the 'Desktop development with
C++' workload (includes cl.exe, rc.exe, and the Windows SDK):
  https://visualstudio.microsoft.com/downloads/  (scroll to 'Tools for Visual Studio')

This is the Windows analog of the macOS build's Xcode Command Line Tools.
Once installed, re-run this script from a normal PowerShell prompt (it will
auto-import the VS environment) or from a 'x64 Native Tools Command Prompt'.
"@
    }
}
if (-not (Get-Command cl.exe -ErrorAction SilentlyContinue)) { Fail 'cl.exe still not on PATH after importing the VS environment.' }
if (-not (Get-Command rc.exe -ErrorAction SilentlyContinue)) { Fail 'rc.exe (Windows SDK) not found. Install the Windows 10/11 SDK component.' }
Info "cl.exe: $((Get-Command cl.exe).Source)"
Info "rc.exe: $((Get-Command rc.exe).Source)"

# ---------------------------------------------------------------------------
# Step 3: Fetch + extract the embeddable CPython (version-locked to the venv)
# ---------------------------------------------------------------------------
Info 'Step 3: Preparing the embedded CPython runtime...'

if (Test-Path $AppRoot) { Remove-Item -Recurse -Force $AppRoot }
New-Item -ItemType Directory -Force -Path $AppRoot | Out-Null
New-Item -ItemType Directory -Force -Path $CacheDir | Out-Null

$EmbedZipName = "python-$PyFull-embed-amd64.zip"
if (-not $PythonEmbedUrl) { $PythonEmbedUrl = "https://www.python.org/ftp/python/$PyFull/$EmbedZipName" }
$CachedZip = Join-Path $CacheDir $EmbedZipName

if (-not (Test-Path $CachedZip)) {
    Info "Downloading $PythonEmbedUrl"
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    try {
        Invoke-WebRequest -Uri $PythonEmbedUrl -OutFile $CachedZip -UseBasicParsing
    } catch {
        Fail "Failed to download the embeddable package for Python $PyFull.`n$($_.Exception.Message)`nProvide it manually via -PythonEmbedUrl or place '$EmbedZipName' in $CacheDir."
    }
} else {
    Info "Using cached $EmbedZipName"
}

Info "Extracting embeddable CPython into $AppRoot"
Expand-Archive -Path $CachedZip -DestinationPath $AppRoot -Force

# The embeddable ships a python3XX._pth that would force an isolated sys.path if
# someone ran the bundled python.exe. Our launcher configures paths explicitly
# via PyConfig and ignores it; remove it so the two mechanisms can't disagree.
Get-ChildItem -Path $AppRoot -Filter '*._pth' -File | Remove-Item -Force -ErrorAction SilentlyContinue

if (-not (Test-Path (Join-Path $AppRoot "python$PyNoDot.dll"))) {
    Fail "python$PyNoDot.dll missing after extraction - the embeddable package may not match Python $PyFull."
}

# ---------------------------------------------------------------------------
# Step 4: Assemble TFM's own code under app\
# ---------------------------------------------------------------------------
Info 'Step 4: Copying TFM source, PuiKit, and LICENSE...'

$AppDir = Join-Path $AppRoot 'app'
New-Item -ItemType Directory -Force -Path $AppDir | Out-Null

function Copy-Tree ($src, $dst) {
    # robocopy exit codes 0-7 indicate success; >=8 is a real failure.
    robocopy $src $dst /E /XD __pycache__ /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { Fail "robocopy failed copying $src -> $dst (code $LASTEXITCODE)" }
    $global:LASTEXITCODE = 0
}

Copy-Item (Join-Path $ProjectRoot 'tfm.py') (Join-Path $AppDir 'tfm.py') -Force
Copy-Tree (Join-Path $ProjectRoot 'src') (Join-Path $AppDir 'src')

# Resolve PuiKit's real source dir from the venv (installed editable), like
# macos_app/build.sh does, so PUIKIT_DIR overrides are honoured.
$PuikitSrc = & $VenvPy -c "import puikit, os; print(os.path.dirname(os.path.abspath(puikit.__file__)))"
if ($LASTEXITCODE -ne 0 -or -not $PuikitSrc -or -not (Test-Path $PuikitSrc)) {
    Fail "PuiKit not importable from the venv (resolved: '$PuikitSrc'). Install it: make install-puikit"
}
Info "PuiKit source: $PuikitSrc"
Copy-Tree $PuikitSrc (Join-Path $AppDir 'puikit')

if (Test-Path (Join-Path $ProjectRoot 'LICENSE')) {
    Copy-Item (Join-Path $ProjectRoot 'LICENSE') (Join-Path $AppDir 'LICENSE') -Force
}

# ---------------------------------------------------------------------------
# Step 5: Collect third-party dependencies into Lib\site-packages
# ---------------------------------------------------------------------------
# Uses the shared, platform-agnostic collector in tools/ (it makes no OS
# assumptions; its PyObjC check self-skips off darwin). It resolves
# the runtime closure of requirements.txt via installed metadata - honouring
# environment markers, so windows-curses is picked up and pyobjc is not.
# --include-deps-of puikit pulls in PuiKit's own runtime deps (numpy, which the
# win32 Direct2D backend imports) without copying PuiKit itself (its source is
# copied into app\puikit above). Each dist is copied with its .dist-info, whose
# license text the notices generator reads in Step 5b.
Info 'Step 5: Collecting third-party dependencies...'

$SitePkgsDest = Join-Path $AppRoot 'Lib\site-packages'
$SharedCollector = Join-Path $ProjectRoot 'tools\collect_dependencies.py'
$Requirements = Join-Path $ProjectRoot 'requirements.txt'
& $VenvPy $SharedCollector --requirements $Requirements --dest $SitePkgsDest --include-deps-of puikit
if ($LASTEXITCODE -ne 0) { Fail 'Dependency collection failed.' }

# ---------------------------------------------------------------------------
# Step 5b: Generate aggregated THIRD_PARTY_NOTICES.txt
# ---------------------------------------------------------------------------
# Reproduces the license text of every bundled Python distribution (scanned from
# their .dist-info under Lib\site-packages) plus the non-distribution components:
# the embedded CPython, the copied-in PuiKit source, and the bundled Noto fonts.
# The generator (shared with macos_app/build.sh) fails the build if any bundled
# distribution has no discoverable license, so an incomplete notice can't ship.
Info 'Step 5b: Generating third-party license notices...'

$NoticesScript = Join-Path $ProjectRoot 'tools\generate_third_party_notices.py'
if (-not (Test-Path $NoticesScript)) { Fail "Notices generator not found at $NoticesScript" }
$NoticesOut = Join-Path $AppRoot 'THIRD_PARTY_NOTICES.txt'
$NoticesExtras = @()

# Embedded interpreter's PSF license (the embeddable ships LICENSE.txt at root).
$PyLicense = Join-Path $AppRoot 'LICENSE.txt'
if (Test-Path $PyLicense) {
    $NoticesExtras += @('--extra', "Python $PyXY interpreter and standard library (Python Software Foundation License Agreement)=$PyLicense")
} else {
    Warn "Embedded Python LICENSE.txt not found at $PyLicense; interpreter will be omitted from notices."
}

# PuiKit's LICENSE lives at the checkout root, one level above the package dir.
$PuikitLicense = Join-Path (Split-Path -Parent $PuikitSrc) 'LICENSE'
if (Test-Path $PuikitLicense) {
    $NoticesExtras += @('--extra', "PuiKit (MIT License)=$PuikitLicense")
} else {
    Fail "PuiKit LICENSE not found at $PuikitLicense"
}

# Bundled fonts (SIL OFL 1.1) - OFL.txt travels inside the copied puikit\fonts.
$FontsOfl = Join-Path $AppDir 'puikit\fonts\OFL.txt'
if (Test-Path $FontsOfl) {
    $NoticesExtras += @('--extra', "Noto Sans & Noto Sans Mono fonts (SIL Open Font License 1.1)=$FontsOfl")
} else {
    Fail "Font license OFL.txt not found at $FontsOfl"
}

$NoticesArgs = @('--title', 'TFM', '--scan', $SitePkgsDest) + $NoticesExtras + @('--output', $NoticesOut)
& $VenvPy $NoticesScript @NoticesArgs
if ($LASTEXITCODE -ne 0) { Fail 'Failed to generate third-party license notices (see errors above).' }

# ---------------------------------------------------------------------------
# Step 6: Pre-compile app + deps to .pyc (launcher runs with write_bytecode=0)
# ---------------------------------------------------------------------------
Info 'Step 6: Pre-compiling Python files...'
& $VenvPy -m compileall -q $AppDir $SitePkgsDest
if ($LASTEXITCODE -ne 0) { Warn 'compileall reported problems (non-fatal).' }

# ---------------------------------------------------------------------------
# Step 7: Build resources and compile the launcher
# ---------------------------------------------------------------------------
Info 'Step 7: Compiling the launcher...'

New-Item -ItemType Directory -Force -Path $ObjDir | Out-Null

# Stage .rc + .manifest into the obj dir so the .rc's relative includes resolve.
Copy-Item (Join-Path $ResDir 'TFM.rc') $ObjDir -Force
Copy-Item (Join-Path $ResDir 'TFM.manifest') $ObjDir -Force

# Generate the .ico (Pillow -> from TFM.icns; else placeholder), preferring a
# hand-authored resources\TFM.ico if one has been committed.
$IcoDest = Join-Path $ObjDir 'TFM.ico'
if (Test-Path (Join-Path $ResDir 'TFM.ico')) {
    Copy-Item (Join-Path $ResDir 'TFM.ico') $IcoDest -Force
    Info 'Using committed resources\TFM.ico'
} else {
    & $VenvPy (Join-Path $ScriptDir 'make_icon.py') --out $IcoDest
    if ($LASTEXITCODE -ne 0) { Warn 'Icon generation failed; continuing without an icon file may break rc.exe.' }
}
# Mirror the final icon into the bundle root too (runtime window icon convenience).
Copy-Item $IcoDest (Join-Path $AppRoot 'TFM.ico') -Force -ErrorAction SilentlyContinue

# Generate version_generated.h from $Version (major,minor,patch,build).
$vparts = @($Version -split '[.\-+]') | Where-Object { $_ -match '^\d+$' }
while ($vparts.Count -lt 4) { $vparts += '0' }
$verHeader = @"
/* Generated by build.ps1 - do not edit. */
#pragma once
#define TFM_VER_MAJOR $($vparts[0])
#define TFM_VER_MINOR $($vparts[1])
#define TFM_VER_PATCH $($vparts[2])
#define TFM_VER_BUILD $($vparts[3])
#define TFM_VER_STR   "$Version"
"@
Set-Content -Path (Join-Path $ObjDir 'version_generated.h') -Value $verHeader -Encoding ASCII

# Compile the resource script -> TFM.res
$ResOut = Join-Path $ObjDir 'TFM.res'
& rc.exe /nologo /fo $ResOut (Join-Path $ObjDir 'TFM.rc')
if ($LASTEXITCODE -ne 0) { Fail 'rc.exe failed.' }

# Compile + link the launcher -> TFM.exe (GUI subsystem, no console).
$ExeOut = Join-Path $AppRoot "$AppName.exe"
$clArgs = @(
    '/nologo', '/O2', '/MD', '/W3',
    "/I$PyInclude",
    (Join-Path $SrcDir 'launcher.c'),
    $ResOut,
    "/Fe:$ExeOut",
    "/Fo:$ObjDir\",
    '/link',
    "/LIBPATH:$PyLibs",
    '/SUBSYSTEM:WINDOWS',
    # We embed our own application manifest via TFM.rc (RT_MANIFEST). Suppress
    # the linker's auto-generated manifest so the exe doesn't end up with two
    # conflicting RT_MANIFEST resources (two <assembly> roots => the SxS loader
    # reports "Invalid Xml syntax" and the app fails to start).
    '/MANIFEST:NO'
)
Info "cl.exe $($clArgs -join ' ')"
& cl.exe @clArgs
if ($LASTEXITCODE -ne 0) { Fail 'cl.exe failed to build the launcher.' }
if (-not (Test-Path $ExeOut)) { Fail "Launcher was not produced at $ExeOut." }

Success "Built $ExeOut"

# ---------------------------------------------------------------------------
# Step 8 (optional): Zip for distribution
# ---------------------------------------------------------------------------
if ($Zip) {
    $ZipOut = Join-Path $BuildDir "TFM-$Version-win64.zip"
    if (Test-Path $ZipOut) { Remove-Item -Force $ZipOut }
    Info "Creating $ZipOut"
    Compress-Archive -Path $AppRoot -DestinationPath $ZipOut -Force
    Success "Created $ZipOut"
}

Write-Host ''
Success 'Build complete.'
Info "Bundle: $AppRoot"
Info "Run it:  & '$ExeOut'"
