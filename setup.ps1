$ErrorActionPreference = "Stop"

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {
    $pythonCmd = @("py", "-3")
} else {
    $python = Get-Command python -ErrorAction Stop
    $pythonCmd = @("python")
}

$version = & $pythonCmd[0] $pythonCmd[1..($pythonCmd.Length - 1)] -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$parts = $version.Trim().Split('.')
if ([int]$parts[0] -lt 3 -or ([int]$parts[0] -eq 3 -and [int]$parts[1] -lt 11)) {
    throw "Python 3.11 or newer is required."
}

$base = Join-Path $env:LOCALAPPDATA "wisp-mcp"
$venv = Join-Path $base "venv"
New-Item -ItemType Directory -Force -Path $base | Out-Null
& $pythonCmd[0] $pythonCmd[1..($pythonCmd.Length - 1)] -m venv $venv
$pythonExe = Join-Path $venv "Scripts\python.exe"
$wispExe = Join-Path $venv "Scripts\wisp-mcp.exe"
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install .
& $wispExe init
& $wispExe doctor
Write-Host ""
Write-Host "Installed executable:"
Write-Host $wispExe
Write-Host ""
Write-Host "Use this command in a local MCP client:"
Write-Host "$wispExe stdio"
