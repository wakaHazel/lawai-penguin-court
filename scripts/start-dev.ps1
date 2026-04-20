$ErrorActionPreference = "Stop"

$rootDir = Split-Path -Parent $PSScriptRoot
$apiDir = Join-Path $rootDir "apps\api"
$webDir = Join-Path $rootDir "apps\web"
$pythonLauncher = "python"
$apiEnvLocal = Join-Path $apiDir ".env.local"

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

if (-not (Test-Path $apiEnvLocal)) {
@"
V3CM_API_KEY=sk-fyBslUC9BeZDrSVS5e3d68A34aE346778111D073E39d971f
V3CM_BASE_URL=https://api.v3.cm/v1
PENGUIN_CG_MODE=static
"@ | Set-Content -Path $apiEnvLocal -Encoding UTF8
}

Stop-ListeningProcessForPort -Port 8000
Stop-ListeningProcessForPort -Port 4173

$apiCommand = @"
Set-Location '$apiDir'
& $pythonLauncher -m pip install -r requirements.txt
& $pythonLauncher -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
"@

$webCommand = @"
Set-Location '$webDir'
if (-not (Test-Path 'node_modules')) { npm install }
npm run dev
"@

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-Command",
    $apiCommand
)

Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-Command",
    $webCommand
)

Write-Host "已启动前后端开发窗口。"
