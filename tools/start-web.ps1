$repo = Split-Path -Parent $PSScriptRoot
$url = 'http://127.0.0.1:4188/'
if (-not (Get-NetTCPConnection -State Listen -LocalPort 4188 -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath 'C:\Program Files\nodejs\npm.cmd' -ArgumentList '--prefix', (Join-Path $repo 'web'), 'run', 'preview' -WorkingDirectory $repo -WindowStyle Hidden
    for ($i = 0; $i -lt 30; $i++) {
        if (Get-NetTCPConnection -State Listen -LocalPort 4188 -ErrorAction SilentlyContinue) { break }
        Start-Sleep -Milliseconds 250
    }
}
Start-Process $url
