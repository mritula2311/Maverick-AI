# =============================================================================
#  MaverickAI — Full Stack Startup Script (Windows PowerShell)
#  Starts: Ollama (LLM), FastAPI Backend, Next.js Frontend
# =============================================================================

$ErrorActionPreference = "Stop"

$RootDir    = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir= Join-Path $RootDir "frontend"
$LogDir     = Join-Path $RootDir "logs"
$OllamaModel= if ($env:OLLAMA_MODEL) { $env:OLLAMA_MODEL } else { "mistral" }

if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

function Write-Banner {
    Write-Host ""
    Write-Host "  +---------------------------------------------------------+" -ForegroundColor Blue
    Write-Host "  |       MaverickAI — Multi-Agent Training Platform        |" -ForegroundColor Blue
    Write-Host "  |      AI-Powered Fresher Onboarding & Assessment         |" -ForegroundColor Cyan
    Write-Host "  |              Hexaware Hackathon 2026                    |" -ForegroundColor Yellow
    Write-Host "  +---------------------------------------------------------+" -ForegroundColor Blue
    Write-Host ""
}

function Log-Info    { param($msg) Write-Host "[INFO]  $msg" -ForegroundColor Green }
function Log-Warn    { param($msg) Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Log-Error   { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }
function Log-Section { param($msg) Write-Host "`n====== $msg ======" -ForegroundColor Blue }

$BackendProcess  = $null
$FrontendProcess = $null
$OllamaProcess   = $null

function Stop-AllServices {
    Write-Host ""
    Log-Warn "Shutting down MaverickAI..."
    if ($BackendProcess  -and -not $BackendProcess.HasExited)  { $BackendProcess.Kill();  Log-Info "Backend stopped" }
    if ($FrontendProcess -and -not $FrontendProcess.HasExited) { $FrontendProcess.Kill(); Log-Info "Frontend stopped" }
    if ($OllamaProcess   -and -not $OllamaProcess.HasExited)   { $OllamaProcess.Kill();   Log-Info "Ollama stopped" }
    Write-Host "`nMaverickAI shut down cleanly. Goodbye!" -ForegroundColor Cyan
}

Write-Banner

# ---------------------------------------------------------------------------
#  PREREQUISITE CHECKS
# ---------------------------------------------------------------------------
Log-Section "Checking Prerequisites"

$PythonCmd = $null
foreach ($cmd in @("python", "python3")) {
    try { $null = & $cmd --version 2>&1; $PythonCmd = $cmd; Log-Info "$cmd found"; break } catch {}
}
if (-not $PythonCmd) { Log-Error "Python 3.11+ is required. Download from https://python.org"; exit 1 }

try { $null = node --version 2>&1; Log-Info "Node.js found: $(node --version)" } catch {
    Log-Error "Node.js 18+ is required. Download from https://nodejs.org"; exit 1
}

$OllamaAvailable = $false
try { $null = ollama --version 2>&1; $OllamaAvailable = $true; Log-Info "Ollama found" } catch {
    Log-Warn "Ollama not found. App will run with mock AI responses."
    Log-Warn "Install from: https://ollama.ai"
}

# ---------------------------------------------------------------------------
#  STEP 1 — OLLAMA
# ---------------------------------------------------------------------------
Log-Section "Step 1: Ollama LLM Server"

if ($OllamaAvailable) {
    $ollamaRunning = $false
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -UseBasicParsing
        if ($resp.StatusCode -eq 200) { $ollamaRunning = $true; Log-Info "Ollama already running" }
    } catch {}

    if (-not $ollamaRunning) {
        Log-Info "Starting Ollama server..."
        $OllamaProcess = Start-Process -FilePath "ollama" -ArgumentList "serve" `
            -PassThru -NoNewWindow -RedirectStandardOutput (Join-Path $LogDir "ollama.log") `
            -RedirectStandardError (Join-Path $LogDir "ollama_err.log")
        Start-Sleep -Seconds 4

        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 3 -UseBasicParsing
            if ($resp.StatusCode -eq 200) { Log-Info "Ollama server started (PID: $($OllamaProcess.Id))" }
        } catch {
            Log-Warn "Ollama did not start in time — using mock responses"
            $OllamaAvailable = $false
        }
    }

    if ($OllamaAvailable) {
        Log-Info "Checking model: $OllamaModel"
        $modelList = ollama list 2>&1
        if ($modelList -match $OllamaModel) {
            Log-Info "Model '$OllamaModel' is ready"
        } else {
            Log-Info "Pulling model '$OllamaModel' (this may take several minutes)..."
            try {
                & ollama pull $OllamaModel 2>&1 | Out-File (Join-Path $LogDir "ollama.log") -Append
                Log-Info "Model '$OllamaModel' downloaded successfully"
            } catch {
                Log-Warn "Could not pull model — app will use mock AI responses"
            }
        }
    }
} else {
    Log-Warn "Skipping Ollama — using built-in mock AI responses"
}

# ---------------------------------------------------------------------------
#  STEP 2 — BACKEND
# ---------------------------------------------------------------------------
Log-Section "Step 2: FastAPI Backend"

Set-Location $BackendDir

# Detect venv python
$VenvPython = $null
foreach ($p in @(".venv\Scripts\python.exe", ".venv\bin\python")) {
    if (Test-Path $p) { $VenvPython = $p; break }
}

if (-not $VenvPython) {
    Log-Info "Creating Python virtual environment..."
    & $PythonCmd -m venv .venv
    $VenvPython = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { ".venv\bin\python" }
}
Log-Info "Using Python: $VenvPython"

Log-Info "Installing/verifying backend dependencies..."
& $VenvPython -m pip install -r requirements.txt -q --no-warn-script-location 2>&1 | Select-Object -Last 3

# Create .env if missing
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
    } else {
        @"
DATABASE_URL=sqlite:///./maverickai.db
SECRET_KEY=maverick-ai-secret-key-change-in-production-2026
ACCESS_TOKEN_EXPIRE_MINUTES=1440
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=neural-chat
OLLAMA_CODE_MODEL=mistral
"@ | Set-Content ".env"
    }
    Log-Info ".env file created"
}

Log-Info "Starting FastAPI backend on http://localhost:8000 ..."
$BackendProcess = Start-Process -FilePath $VenvPython `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" `
    -PassThru -NoNewWindow `
    -RedirectStandardOutput (Join-Path $LogDir "backend.log") `
    -RedirectStandardError  (Join-Path $LogDir "backend_err.log") `
    -WorkingDirectory $BackendDir

Log-Info "Waiting for backend to start..."
$ready = $false
for ($i = 1; $i -le 20; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -UseBasicParsing
        if ($r.StatusCode -eq 200) { $ready = $true; Log-Info "Backend is ready! (PID: $($BackendProcess.Id))"; break }
    } catch {}
}
if (-not $ready) {
    Log-Error "Backend failed to start. Check $(Join-Path $LogDir 'backend_err.log')"
    Get-Content (Join-Path $LogDir "backend_err.log") -Tail 20
    Stop-AllServices; exit 1
}

# ---------------------------------------------------------------------------
#  STEP 3 — FRONTEND
# ---------------------------------------------------------------------------
Log-Section "Step 3: Next.js Frontend"

Set-Location $FrontendDir

# Create .env.local if missing
if (-not (Test-Path ".env.local")) {
    "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" | Set-Content ".env.local"
    Log-Info "Frontend .env.local created"
}

if (-not (Test-Path "node_modules")) {
    Log-Info "Installing frontend dependencies (this may take a minute)..."
    npm install --legacy-peer-deps --loglevel warn 2>&1 | Select-Object -Last 5
} else {
    Log-Info "Frontend dependencies already installed"
}

Log-Info "Starting Next.js frontend on http://localhost:3000 ..."
$FrontendProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" `
    -PassThru -NoNewWindow `
    -RedirectStandardOutput (Join-Path $LogDir "frontend.log") `
    -RedirectStandardError  (Join-Path $LogDir "frontend_err.log") `
    -WorkingDirectory $FrontendDir

Log-Info "Waiting for frontend to start..."
$ready = $false
for ($i = 1; $i -le 30; $i++) {
    Start-Sleep -Seconds 2
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 3 -UseBasicParsing
        if ($r.StatusCode -eq 200) { $ready = $true; Log-Info "Frontend is ready! (PID: $($FrontendProcess.Id))"; break }
    } catch {}
}
if (-not $ready) {
    Log-Warn "Frontend may still be compiling — check http://localhost:3000 in a moment"
}

# ---------------------------------------------------------------------------
#  STARTUP COMPLETE
# ---------------------------------------------------------------------------
Log-Section "MaverickAI is Running"

Write-Host ""
Write-Host "  Application URLs:" -ForegroundColor Green
Write-Host "  Frontend   -->  http://localhost:3000" -ForegroundColor Cyan
Write-Host "  Backend    -->  http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API Docs   -->  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Ollama     -->  http://localhost:11434  $(if ($OllamaAvailable) { '(active)' } else { '(mock mode)' })" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Default Login Credentials:" -ForegroundColor Green
Write-Host "  Fresher  -->  alice@maverick.ai    /  password123" -ForegroundColor Yellow
Write-Host "  Manager  -->  manager@maverick.ai  /  password123" -ForegroundColor Yellow
Write-Host "  Admin    -->  admin@maverick.ai    /  admin123" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Logs saved to: $LogDir\" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Press Ctrl+C to stop all services" -ForegroundColor Red
Write-Host ""

try {
    # Keep the script alive and show live backend logs
    Get-Content (Join-Path $LogDir "backend.log") -Wait
} finally {
    Stop-AllServices
}
