[CmdletBinding()]
param(
    [ValidateSet('future_courtyard')][string]$Asset = 'future_courtyard',
    [ValidateSet('all','turntable')][string]$Stage = 'all'
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$blender = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
$python = Join-Path $env:APPDATA 'uv\python\cpython-3.11-windows-x86_64-none\python.exe'
if (-not (Test-Path -LiteralPath $blender)) { throw 'Blender 5.2 not found.' }
if (-not (Test-Path -LiteralPath $python)) { throw 'uv-managed Python 3.11 not found.' }
$extra = @()
if ($Stage -eq 'turntable') { $extra += '--turntable' }
Push-Location $repo
try {
    & $blender --background --python 'blender/scripts/build_future_courtyard.py' -- @extra
    if ($LASTEXITCODE -ne 0) { throw "Blender build failed: $LASTEXITCODE" }
    & $python 'tools/validate_assets.py' --promote
    if ($LASTEXITCODE -ne 0) { throw "Asset gate failed: $LASTEXITCODE" }
    'Asset build and promotion passed.'
} finally { Pop-Location }
