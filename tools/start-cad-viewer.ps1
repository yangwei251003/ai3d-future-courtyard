$repo = Split-Path -Parent $PSScriptRoot
$skill = Join-Path $env:USERPROFILE '.codex\skills\cad-viewer\scripts\viewer'
if (-not (Test-Path -LiteralPath $skill)) { throw 'CAD Viewer skill runtime not found.' }
if (-not (Get-NetTCPConnection -State Listen -LocalPort 3245 -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath 'C:\Program Files\nodejs\npm.cmd' -ArgumentList '--prefix', $skill, 'run', 'start', '--', '--host', '127.0.0.1' -WorkingDirectory $repo -WindowStyle Hidden
    for ($i = 0; $i -lt 40; $i++) {
        if (Get-NetTCPConnection -State Listen -LocalPort 3245 -ErrorAction SilentlyContinue) { break }
        Start-Sleep -Milliseconds 250
    }
}
$base = 'http://127.0.0.1:3245/' + [Uri]::EscapeDataString($repo.Replace('\','/')).Replace('%2F','/')
Start-Process "${base}?file=assets/runtime/future_courtyard_environment.glb"
Start-Process "${base}?file=assets/runtime/future_courtyard_character.glb"
