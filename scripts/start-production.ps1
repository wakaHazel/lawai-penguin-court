$ErrorActionPreference = "Stop"

$rootDir = Split-Path -Parent $PSScriptRoot
$apiDir = Join-Path $rootDir "apps\api"
$webDir = Join-Path $rootDir "apps\web"
$pythonLauncher = "python"
$port = if ($env:PORT) { $env:PORT } else { "8000" }

function Stop-ListeningProcessForPort {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $processIds = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
        Where-Object { $_.LocalPort -eq $Port } |
        Select-Object -ExpandProperty OwningProcess -Unique

    foreach ($processId in $processIds) {
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
}

Stop-ListeningProcessForPort -Port ([int]$port)

Set-Location $webDir
if (-not (Test-Path "node_modules")) {
    npm install
}
npm run build

Set-Location $apiDir
& $pythonLauncher -m uvicorn app.main:app --host 0.0.0.0 --port $port
