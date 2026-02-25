#!/usr/bin/env bash
set -euo pipefail

# ─── SignalCore Vendor Research Tool — Full Stack Run Script ───
# Starts both the backend API server and the frontend dev server.

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$REPO_ROOT/vendor-research-tool-backend"
FRONTEND_DIR="$REPO_ROOT/vendor-research-tool-frontend"

echo "======================================"
echo "  SignalCore Vendor Research Tool"
echo "======================================"
echo ""

# ─── Check prerequisites ───

if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 not found. Install Python 3.11+"
  exit 1
fi

if ! command -v node &>/dev/null; then
  echo "ERROR: node not found. Install Node.js 20+"
  exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
NODE_VERSION=$(node --version)
echo "[OK] Python $PYTHON_VERSION"
echo "[OK] Node $NODE_VERSION"

# ─── Setup Python venv ───

VENV_DIR="$REPO_ROOT/venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "[...] Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
echo "[OK] Virtual environment activated"

# ─── Install backend dependencies ───

echo "[...] Installing backend dependencies..."
pip install -q -r "$BACKEND_DIR/requirements.txt"

# ─── Install frontend dependencies ───

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  echo "[...] Installing frontend dependencies..."
  (cd "$FRONTEND_DIR" && npm install)
else
  echo "[OK] Frontend dependencies already installed"
fi

# ─── Check backend .env ───

if [ ! -f "$BACKEND_DIR/.env" ]; then
  if [ -f "$BACKEND_DIR/.env.example" ]; then
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
    echo ""
    echo "[WARN] Created backend .env from .env.example"
    echo "       Edit $BACKEND_DIR/.env with your API keys:"
    echo "       - TAVILY_API_KEY (required)"
    echo "       - LLM provider key (OPENROUTER_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY)"
    exit 1
  else
    echo "ERROR: No .env file found in backend. Create one from .env.example"
    exit 1
  fi
fi

# ─── Check port availability ───

BACKEND_PORT=8000
FRONTEND_PORT=5173

for PORT_NAME in "Backend:$BACKEND_PORT" "Frontend:$FRONTEND_PORT"; do
  NAME="${PORT_NAME%%:*}"
  PORT="${PORT_NAME##*:}"
  if lsof -ti:$PORT &>/dev/null; then
    echo "[WARN] $NAME port $PORT is already in use"
    PIDS=$(lsof -ti:$PORT)
    read -rp "       Kill existing processes on port $PORT? [Y/n] " REPLY
    REPLY=${REPLY:-Y}
    if [[ "$REPLY" =~ ^[Yy]$ ]]; then
      kill $PIDS 2>/dev/null || true
      sleep 1
      if lsof -ti:$PORT &>/dev/null; then
        kill -9 $(lsof -ti:$PORT) 2>/dev/null || true
        sleep 1
      fi
      echo "[OK] Port $PORT freed"
    else
      echo "       Aborting."
      exit 1
    fi
  fi
done

# ─── Database status ───

mkdir -p "$BACKEND_DIR/data"
if [ -f "$BACKEND_DIR/data/research.db" ]; then
  JOB_COUNT=$(python3 -c "
import sqlite3
conn = sqlite3.connect('$BACKEND_DIR/data/research.db')
count = conn.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
print(count)
conn.close()
" 2>/dev/null || echo "0")
  echo "[OK] Database: $JOB_COUNT previous job(s)"
else
  echo "[INFO] No database yet — will be created on first startup"
fi

# ─── Start both servers ───

echo ""
echo "======================================"
echo "  Starting servers..."
echo "  Backend API:  http://localhost:$BACKEND_PORT/api/"
echo "  Health check: http://localhost:$BACKEND_PORT/health"
echo "  Frontend UI:  http://localhost:$FRONTEND_PORT/"
echo ""
echo "  Press Ctrl+C to stop both servers"
echo "======================================"
echo ""

# Start backend in background
(cd "$BACKEND_DIR" && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT) &
BACKEND_PID=$!

# Start frontend in background
(cd "$FRONTEND_DIR" && npm run dev -- --host 0.0.0.0 --port $FRONTEND_PORT) &
FRONTEND_PID=$!

# Cleanup on exit
cleanup() {
  echo ""
  echo "Shutting down..."
  kill $BACKEND_PID 2>/dev/null || true
  kill $FRONTEND_PID 2>/dev/null || true
  wait 2>/dev/null
  echo "Done."
}
trap cleanup EXIT INT TERM

# Wait for both
wait
