[CmdletBinding()]
param([ValidateSet('future_courtyard')][string]$Asset = 'future_courtyard')

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$godot = Join-Path $env:LOCALAPPDATA 'Programs\Godot\4.7.2\Godot_v4.7.2-stable_win64_console.exe'
$python = Join-Path $env:APPDATA 'uv\python\cpython-3.11-windows-x86_64-none\python.exe'
$uv = Join-Path $env:USERPROFILE '.local\bin\uv.exe'
$tmp = Join-Path $repo 'evidence\tmp'
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
Push-Location $repo
try {
    & "$PSScriptRoot\doctor.ps1" | Tee-Object -FilePath "$tmp\doctor.txt"
    if ($LASTEXITCODE -ne 0) { throw 'G0 doctor failed.' }
    & $uv run --python 3.11 --with pyyaml (Join-Path $env:USERPROFILE '.codex\skills\.system\skill-creator\scripts\quick_validate.py') '.agents\skills\3d-production-pipeline' | Tee-Object -FilePath "$tmp\skill-validation.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Project skill validation failed.' }
    & $python '.agents\skills\3d-production-pipeline\scripts\check_contract.py' '.' | Tee-Object -FilePath "$tmp\contract-validation.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Brief contract failed.' }
    & $python 'tools\validate_assets.py' | Tee-Object -FilePath "$tmp\asset-validation.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Canonical asset validation failed.' }
    & npm run gltf:validate | Tee-Object -FilePath "$tmp\gltf-transform.txt"
    if ($LASTEXITCODE -ne 0) { throw 'glTF-Transform validation failed.' }
    & $godot --headless --editor --path $repo --quit-after 3 | Tee-Object -FilePath "$tmp\godot-import.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Godot import failed.' }
    & $godot --headless --path $repo --script 'res://game/tests/smoke_test.gd' | Tee-Object -FilePath "$tmp\godot-smoke.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Godot gameplay smoke failed.' }
    & node 'tools\godot-mcp-e2e.mjs' | Tee-Object -FilePath "$tmp\godot-mcp-runtime.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Godot MCP runtime gate failed.' }
    & npm --prefix web run build | Tee-Object -FilePath "$tmp\web-build.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Web build failed.' }
    & npm --prefix web run test:e2e | Tee-Object -FilePath "$tmp\web-test.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Web E2E failed.' }
    & $python 'tools\write_receipts.py'
    if ($LASTEXITCODE -ne 0) { throw 'Receipt finalization failed.' }
    'G0-G7 verification passed.'
} finally { Pop-Location }
