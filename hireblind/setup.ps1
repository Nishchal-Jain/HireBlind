$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path  # ...\hireblind
$workspaceRoot = Split-Path $root -Parent  # ...\HireBlind (contains the `hireblind/` package)
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"

Write-Host "== HireBlind local setup ==" -ForegroundColor Cyan

# 1) Ensure Python version (recommended: 3.12)
function Test-PythonVersion {
  param([string]$Version)
  try {
    $out = py -$Version -c "import sys; print(sys.version_info[:3])" 2>$null
    return ($out -match "\(\d+,\s*\d+,\s*\d+\)")
  } catch {
    return $false
  }
}

$pythonVersion = $null
if (Test-PythonVersion -Version "3.12") { $pythonVersion = "3.12" }
elseif (Test-PythonVersion -Version "3.11") { $pythonVersion = "3.11" }
else { $pythonVersion = $null }

if (-not $pythonVersion) {
  Write-Host "Python 3.12 (or 3.11) was not found via the Windows `py` launcher." -ForegroundColor Yellow
  Write-Host "Install Python 3.12, then rerun:" -ForegroundColor Yellow
  Write-Host "  py -3.12 --version" -ForegroundColor Yellow
  exit 1
}

Write-Host "Using Python $pythonVersion from `py`." -ForegroundColor Green

# 2) Backend: create venv + install deps
$venv = Join-Path $backendDir ".venv"
$needRecreate = $true
if (Test-Path $venv) {
  try {
    $venvPy = Join-Path $venv "Scripts\python.exe"
    if (Test-Path $venvPy) {
      $out = & $venvPy -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>$null
      if ($out -eq $pythonVersion) {
        $needRecreate = $false
      } else {
        $needRecreate = $true
      }
    }
  } catch {
    $needRecreate = $true
  }
}

if ($needRecreate) {
  if (Test-Path $venv) {
    Write-Host "Recreating backend venv (Python mismatch)..." -ForegroundColor Yellow
    try {
      Remove-Item -Recurse -Force $venv
    } catch {
      Write-Host "Could not remove existing venv due to file locks/permissions." -ForegroundColor Red
      Write-Host "Please close any running backend processes and rerun." -ForegroundColor Yellow
      exit 1
    }
  }

  Write-Host "Creating backend venv..." -ForegroundColor Cyan
  py -$pythonVersion -m venv $venv
} else {
  Write-Host "Backend venv already exists with Python $pythonVersion." -ForegroundColor Green
}

$venvPy = Join-Path $venv "Scripts\python.exe"

Write-Host "Ensuring pip exists in backend venv..." -ForegroundColor Cyan
try {
  & $venvPy -c "import pip" 2>$null | Out-Null
} catch {
  & $venvPy -m ensurepip --upgrade | Out-Null
}

Write-Host "Installing backend dependencies..." -ForegroundColor Cyan
& $venvPy -m pip install --upgrade pip
& $venvPy -m pip install -r "$backendDir\requirements.txt"

# 3) Frontend: npm install
Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
  Push-Location $frontendDir
  npm install
  Pop-Location
}

Write-Host "Starting servers..." -ForegroundColor Cyan

# Start backend (FastAPI)
# Start from the workspace root so `hireblind.backend.main:app` can be imported.
Push-Location $workspaceRoot
$backendProcess = Start-Process -NoNewWindow -FilePath "$venv\Scripts\python.exe" -ArgumentList "-m","uvicorn","hireblind.backend.main:app","--reload","--port","8000" -PassThru
Pop-Location

# Start frontend (Vite)
Push-Location $frontendDir
$frontendProcess = Start-Process -NoNewWindow -FilePath "cmd.exe" -ArgumentList "/c","npm","run","dev" -PassThru
Pop-Location

Write-Host "Backend:  http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green

Write-Host "Tip: backend logs are in the spawned process windows." -ForegroundColor Yellow

