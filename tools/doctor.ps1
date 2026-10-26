[CmdletBinding()]
param([switch]$JsonOnly)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$godot = Join-Path $env:LOCALAPPDATA 'Programs\Godot\4.7.2\Godot_v4.7.2-stable_win64_console.exe'
$ffmpeg = Join-Path $env:LOCALAPPDATA 'Programs\FFmpeg\8.1.2\ffmpeg-8.1.2-essentials_build\bin\ffmpeg.exe'
$ffprobe = Join-Path $env:LOCALAPPDATA 'Programs\FFmpeg\8.1.2\ffmpeg-8.1.2-essentials_build\bin\ffprobe.exe'
$uv = Join-Path $env:USERPROFILE '.local\bin\uv.exe'
$uvx = Join-Path $env:USERPROFILE '.local\bin\uvx.exe'
$lfs = 'C:\Program Files\Git LFS\git-lfs.exe'
$stableCodex = Join-Path $env:LOCALAPPDATA 'Programs\CodexCLI\0.151.0\node_modules\.bin\codex.cmd'
$codex = if (Test-Path -LiteralPath $stableCodex) { $stableCodex } else { Get-ChildItem -LiteralPath (Join-Path $env:LOCALAPPDATA 'OpenAI\Codex\bin') -Filter codex.exe -Recurse -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName }
$blender = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'

$checks = [ordered]@{}
function Add-Check([string]$Name, [bool]$Pass, [string]$Actual) {
    $script:checks[$Name] = [ordered]@{ pass = $Pass; actual = $Actual }
}

Add-Check 'unicodeWorkspace' ($repo -like '*AI3D仓库') $repo
Add-Check 'blender' (Test-Path -LiteralPath $blender) $(if (Test-Path $blender) { (& $blender --version | Select-Object -First 1) } else { 'missing' })
Add-Check 'godot' (Test-Path -LiteralPath $godot) $(if (Test-Path $godot) { (& $godot --version) } else { 'missing' })
Add-Check 'ffmpeg' (Test-Path -LiteralPath $ffmpeg) $(if (Test-Path $ffmpeg) { (& $ffmpeg -version | Select-Object -First 1) } else { 'missing' })
Add-Check 'ffprobe' (Test-Path -LiteralPath $ffprobe) $(if (Test-Path $ffprobe) { (& $ffprobe -version | Select-Object -First 1) } else { 'missing' })
Add-Check 'git' ($null -ne (Get-Command git -ErrorAction SilentlyContinue)) $(& git --version)
Add-Check 'gitLfs' (Test-Path -LiteralPath $lfs) $(if (Test-Path $lfs) { (& $lfs version) } else { 'missing' })
Add-Check 'node' ($null -ne (Get-Command node -ErrorAction SilentlyContinue)) $(& node --version)
Add-Check 'uv' (Test-Path -LiteralPath $uv) $(if (Test-Path $uv) { (& $uv --version) } else { 'missing' })
Add-Check 'uvx' (Test-Path -LiteralPath $uvx) $(if (Test-Path $uvx) { $uvx } else { 'missing' })
Add-Check 'codex' ($null -ne $codex) $(if ($codex) { (& $codex --version) } else { 'missing' })
Add-Check 'projectMcpConfig' (Test-Path -LiteralPath (Join-Path $repo '.codex\config.toml')) '.codex/config.toml'
Add-Check 'blenderBridgePort9876' ($null -ne (Get-NetTCPConnection -State Listen -LocalPort 9876 -ErrorAction SilentlyContinue)) 'localhost:9876'
Add-Check 'blenderMcpSmokeEvidence' (Test-Path -LiteralPath (Join-Path $repo 'evidence\mcp\blender-mcp-smoke.json')) 'evidence/mcp/blender-mcp-smoke.json'

$result = [ordered]@{
    gateId = 'G0'
    status = $(if (($checks.Values.pass -notcontains $false)) { 'pass' } else { 'fail' })
    inputHashes = [ordered]@{}
    toolVersions = [ordered]@{
        blender = $checks.blender.actual
        godot = $checks.godot.actual
        git = $checks.git.actual
        gitLfs = $checks.gitLfs.actual
        node = $checks.node.actual
        uv = $checks.uv.actual
        codex = $checks.codex.actual
    }
    assertions = @($checks.GetEnumerator() | ForEach-Object { [ordered]@{ name = $_.Key; pass = $_.Value.pass; actual = $_.Value.actual } })
    evidencePaths = @('evidence/gates/G0-environment.json', '.codex/config.toml')
    failureCategory = $(if (($checks.Values.pass -notcontains $false)) { $null } else { 'environment' })
    recoveryFrom = $null
    checkedAt = (Get-Date).ToUniversalTime().ToString('o')
    checks = $checks
}
$gateDir = Join-Path $repo 'evidence\gates'
New-Item -ItemType Directory -Force -Path $gateDir | Out-Null
$json = $result | ConvertTo-Json -Depth 8
Set-Content -LiteralPath (Join-Path $gateDir 'G0-environment.json') -Value $json -Encoding utf8
if ($JsonOnly) { $json } else {
    $checks.GetEnumerator() | ForEach-Object { "[{0}] {1}: {2}" -f $(if ($_.Value.pass) {'PASS'} else {'FAIL'}), $_.Key, $_.Value.actual }
    "G0=$($result.status)"
}
if ($result.status -ne 'pass') { exit 1 }
