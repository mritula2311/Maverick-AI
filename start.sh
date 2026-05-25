#!/usr/bin/env bash
# =============================================================================
#  MaverickAI — Full Stack Startup Script
#  Starts: Ollama (LLM), FastAPI Backend, Next.js Frontend
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$ROOT_DIR/logs"
OLLAMA_MODEL="${OLLAMA_MODEL:-mistral}"

mkdir -p "$LOG_DIR"

print_banner() {
  echo -e "${BLUE}${BOLD}"
  echo "  ███╗   ███╗ █████╗ ██╗   ██╗███████╗██████╗ ██╗ ██████╗██╗  ██╗ █████╗ ██╗"
  echo "  ████╗ ████║██╔══██╗██║   ██║██╔════╝██╔══██╗██║██╔════╝██║ ██╔╝██╔══██╗██║"
  echo "  ██╔████╔██║███████║██║   ██║█████╗  ██████╔╝██║██║     █████╔╝ ███████║██║"
  echo "  ██║╚██╔╝██║██╔══██║╚██╗ ██╔╝██╔══╝  ██╔══██╗██║██║     ██╔═██╗ ██╔══██║██║"
  echo "  ██║ ╚═╝ ██║██║  ██║ ╚████╔╝ ███████╗██║  ██║██║╚██████╗██║  ██╗██║  ██║██║"
  echo "  ╚═╝     ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝"
  echo -e "${NC}"
  echo -e "  ${CYAN}AI-Powered Fresher Onboarding & Training Management Platform${NC}"
  echo -e "  ${YELLOW}Hexaware Hackathon 2026${NC}"
  echo ""
}

log_info()    { echo -e "${GREEN}[INFO]${NC}  $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
log_section() { echo -e "\n${BLUE}${BOLD}══════ $1 ══════${NC}"; }

# ---------------------------------------------------------------------------
#  CLEANUP on exit
# ---------------------------------------------------------------------------
cleanup() {
  echo ""
  log_warn "Shutting down MaverickAI..."

  [ -n "$BACKEND_PID" ]  && kill "$BACKEND_PID"  2>/dev/null && log_info "Backend stopped"
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null && log_info "Frontend stopped"

  # Stop Ollama serve if we started it
  if [ -n "$OLLAMA_PID" ]; then
    kill "$OLLAMA_PID" 2>/dev/null
    log_info "Ollama stopped"
  fi

  echo ""
  echo -e "${CYAN}MaverickAI shut down cleanly. Goodbye!${NC}"
}
trap cleanup SIGINT SIGTERM EXIT

# ---------------------------------------------------------------------------
#  PREREQUISITE CHECKS
# ---------------------------------------------------------------------------
log_section "Checking Prerequisites"

check_command() {
  if command -v "$1" &>/dev/null; then
    log_info "$1 found: $(command -v "$1")"
    return 0
  else
    return 1
  fi
}

# Python
if check_command python3; then
  PYTHON=python3
elif check_command python; then
  PYTHON=python
else
  log_error "Python 3.11+ is required. Install from https://python.org"
  exit 1
fi

# Node.js
if ! check_command node; then
  log_error "Node.js 18+ is required. Install from https://nodejs.org"
  exit 1
fi

# npm
if ! check_command npm; then
  log_error "npm is required. It comes bundled with Node.js."
  exit 1
fi

# Ollama
OLLAMA_AVAILABLE=false
if check_command ollama; then
  OLLAMA_AVAILABLE=true
else
  log_warn "Ollama not found. The app will run with mock AI responses."
  log_warn "Install Ollama from: https://ollama.ai"
fi

# ---------------------------------------------------------------------------
#  STEP 1 — START OLLAMA
# ---------------------------------------------------------------------------
log_section "Step 1: Ollama LLM Server"

if [ "$OLLAMA_AVAILABLE" = true ]; then
  # Check if Ollama is already running
  if curl -s --max-time 2 http://localhost:11434/api/tags &>/dev/null; then
    log_info "Ollama is already running on port 11434"
  else
    log_info "Starting Ollama server..."
    ollama serve > "$LOG_DIR/ollama.log" 2>&1 &
    OLLAMA_PID=$!
    sleep 3

    if curl -s --max-time 2 http://localhost:11434/api/tags &>/dev/null; then
      log_info "Ollama server started (PID: $OLLAMA_PID)"
    else
      log_warn "Ollama server did not start in time — continuing with mock responses"
      OLLAMA_AVAILABLE=false
    fi
  fi

  # Pull the model if not available
  if [ "$OLLAMA_AVAILABLE" = true ]; then
    log_info "Checking for model: $OLLAMA_MODEL"
    if ollama list 2>/dev/null | grep -q "$OLLAMA_MODEL"; then
      log_info "Model '$OLLAMA_MODEL' is ready"
    else
      log_info "Pulling model '$OLLAMA_MODEL' (this may take a few minutes)..."
      if ollama pull "$OLLAMA_MODEL" >> "$LOG_DIR/ollama.log" 2>&1; then
        log_info "Model '$OLLAMA_MODEL' downloaded successfully"
      else
        log_warn "Could not pull model '$OLLAMA_MODEL' — check your internet connection"
        log_warn "The app will fall back to built-in mock responses"
      fi
    fi
  fi
else
  log_warn "Skipping Ollama — using built-in mock AI responses for evaluation"
fi

# ---------------------------------------------------------------------------
#  STEP 2 — BACKEND SETUP
# ---------------------------------------------------------------------------
log_section "Step 2: FastAPI Backend"

cd "$BACKEND_DIR"

# Detect virtual environment
if [ -d ".venv" ]; then
  if [ -f ".venv/Scripts/python.exe" ]; then
    VENV_PYTHON=".venv/Scripts/python.exe"   # Windows Git Bash
    VENV_PIP=".venv/Scripts/pip.exe"
  elif [ -f ".venv/bin/python" ]; then
    VENV_PYTHON=".venv/bin/python"            # Linux/Mac
    VENV_PIP=".venv/bin/pip"
  fi
  log_info "Using existing virtual environment"
else
  log_info "Creating Python virtual environment..."
  $PYTHON -m venv .venv
  if [ -f ".venv/Scripts/python.exe" ]; then
    VENV_PYTHON=".venv/Scripts/python.exe"
    VENV_PIP=".venv/Scripts/pip.exe"
  else
    VENV_PYTHON=".venv/bin/python"
    VENV_PIP=".venv/bin/pip"
  fi
fi

# Install dependencies
log_info "Installing/verifying backend dependencies..."
"$VENV_PIP" install -r requirements.txt -q --no-warn-script-location 2>&1 | tail -3

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
  log_info "Creating .env from .env.example..."
  cp .env.example .env 2>/dev/null || cat > .env << 'ENVEOF'
DATABASE_URL=sqlite:///./maverickai.db
SECRET_KEY=maverick-ai-secret-key-change-in-production-2026
ACCESS_TOKEN_EXPIRE_MINUTES=1440
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=neural-chat
OLLAMA_CODE_MODEL=mistral
ENVEOF
  log_info ".env file created"
fi

# Start backend
log_info "Starting FastAPI backend on http://localhost:8000 ..."

if [ -f ".venv/Scripts/uvicorn.exe" ]; then
  UVICORN=".venv/Scripts/uvicorn.exe"
elif [ -f ".venv/bin/uvicorn" ]; then
  UVICORN=".venv/bin/uvicorn"
else
  UVICORN="$VENV_PYTHON -m uvicorn"
fi

$VENV_PYTHON -m uvicorn app.main:app --host 0.0.0.0 --port 8000 \
  > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

# Wait for backend to be ready
log_info "Waiting for backend to start..."
for i in {1..20}; do
  if curl -s --max-time 2 http://localhost:8000/health &>/dev/null; then
    log_info "Backend is ready! (PID: $BACKEND_PID)"
    break
  fi
  if [ $i -eq 20 ]; then
    log_error "Backend failed to start. Check $LOG_DIR/backend.log"
    cat "$LOG_DIR/backend.log" | tail -20
    exit 1
  fi
  sleep 1
done

# ---------------------------------------------------------------------------
#  STEP 3 — FRONTEND SETUP
# ---------------------------------------------------------------------------
log_section "Step 3: Next.js Frontend"

cd "$FRONTEND_DIR"

# Create .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
  log_info "Creating frontend .env.local..."
  cat > .env.local << 'FRONTENVEOF'
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
FRONTENVEOF
  log_info "Frontend .env.local created"
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
  log_info "Installing frontend dependencies (this may take a minute)..."
  npm install --legacy-peer-deps --loglevel warn 2>&1 | tail -5
else
  log_info "Frontend dependencies already installed"
fi

# Start Next.js
log_info "Starting Next.js frontend on http://localhost:3000 ..."
npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to be ready
log_info "Waiting for frontend to start..."
for i in {1..30}; do
  if curl -s --max-time 2 http://localhost:3000 &>/dev/null; then
    log_info "Frontend is ready! (PID: $FRONTEND_PID)"
    break
  fi
  if [ $i -eq 30 ]; then
    log_error "Frontend failed to start. Check $LOG_DIR/frontend.log"
    cat "$LOG_DIR/frontend.log" | tail -20
    exit 1
  fi
  sleep 2
done

# ---------------------------------------------------------------------------
#  STARTUP COMPLETE
# ---------------------------------------------------------------------------
log_section "MaverickAI is Running"

echo ""
echo -e "  ${GREEN}${BOLD}Application URLs:${NC}"
echo -e "  ${CYAN}Frontend   →  http://localhost:3000${NC}"
echo -e "  ${CYAN}Backend    →  http://localhost:8000${NC}"
echo -e "  ${CYAN}API Docs   →  http://localhost:8000/docs${NC}"
echo -e "  ${CYAN}Ollama     →  http://localhost:11434${NC}  $([ "$OLLAMA_AVAILABLE" = true ] && echo "(active)" || echo "(mock mode)")"
echo ""
echo -e "  ${GREEN}${BOLD}Default Login Credentials:${NC}"
echo -e "  ${YELLOW}Fresher  →  alice@maverick.ai   /  password123${NC}"
echo -e "  ${YELLOW}Manager  →  manager@maverick.ai /  password123${NC}"
echo -e "  ${YELLOW}Admin    →  admin@maverick.ai   /  admin123${NC}"
echo ""
echo -e "  ${YELLOW}Logs saved to: $LOG_DIR/${NC}"
echo ""
echo -e "  ${RED}Press Ctrl+C to stop all services${NC}"
echo ""

# ---------------------------------------------------------------------------
#  KEEP ALIVE — tail backend log so output stays visible
# ---------------------------------------------------------------------------
wait $BACKEND_PID $FRONTEND_PID
