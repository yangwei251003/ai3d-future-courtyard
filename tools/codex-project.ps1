[CmdletBinding()]
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)

$repo = Split-Path -Parent $PSScriptRoot
$codex = Join-Path $env:LOCALAPPDATA 'Programs\CodexCLI\0.151.0\node_modules\.bin\codex.cmd'
if (-not (Test-Path -LiteralPath $codex)) { throw 'Codex CLI 0.151.0 not found. Run tools/doctor.ps1.' }
& $codex -C $repo @Arguments
exit $LASTEXITCODE
