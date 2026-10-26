$repo = Split-Path -Parent $PSScriptRoot
$godot = Join-Path $env:LOCALAPPDATA 'Programs\Godot\4.7.2\Godot_v4.7.2-stable_win64.exe'
if (-not (Test-Path -LiteralPath $godot)) { throw 'Godot 4.7.2 not found.' }
Start-Process -FilePath $godot -ArgumentList '--path', $repo
& "$PSScriptRoot\start-web.ps1"
