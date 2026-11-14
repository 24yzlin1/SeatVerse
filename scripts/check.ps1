#Requires -Version 5.1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Push-Location (Join-Path $root "frontend")
try {
    Write-Host "==> frontend check"
    & npm.cmd run check
    if ($LASTEXITCODE -ne 0) { throw "frontend check failed (exit $LASTEXITCODE)" }

    Write-Host "==> frontend lint"
    & npm.cmd run lint
    if ($LASTEXITCODE -ne 0) { throw "frontend lint failed (exit $LASTEXITCODE)" }

    Write-Host "==> frontend build"
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw "frontend build failed (exit $LASTEXITCODE)" }
} finally {
    Pop-Location
}

$backend = Join-Path $root "backend"
$poe = Join-Path $backend ".venv\Scripts\poe.exe"
if (-not (Test-Path $poe)) {
    throw "backend virtual environment not found; run 'uv sync' in backend first"
}

Push-Location $backend
try {
    Write-Host "==> backend mypy"
    & $poe check
    if ($LASTEXITCODE -ne 0) { throw "backend mypy failed (exit $LASTEXITCODE)" }

    Write-Host "==> backend pytest"
    & $poe test
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 5) {
        throw "backend pytest failed (exit $LASTEXITCODE)"
    }
} finally {
    Pop-Location
}

Write-Host "ALL GREEN"
