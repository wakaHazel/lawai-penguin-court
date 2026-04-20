$ErrorActionPreference = "Stop"

$rootDir = Split-Path -Parent $PSScriptRoot
$port = if ($env:PORT) { $env:PORT } else { "8000" }

function Ensure-ListeningOnPort {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $listening = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
        Where-Object { $_.LocalPort -eq $Port } |
        Select-Object -First 1

    if ($null -ne $listening) {
        return
    }

    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        (Join-Path $PSScriptRoot "start-production.ps1")
    )

    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Seconds 1
        $listening = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
            Where-Object { $_.LocalPort -eq $Port } |
            Select-Object -First 1
        if ($null -ne $listening) {
            return
        }
    }

    throw "完整服务未能在端口 $Port 上启动。"
}

Ensure-ListeningOnPort -Port ([int]$port)

Set-Location $rootDir
npx -y localtunnel --port $port
