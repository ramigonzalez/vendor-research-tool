#!/usr/bin/env bash
set -euo pipefail

# ─── SignalCore Vendor Research Tool — Run Script ───

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "======================================"
echo "  SignalCore Vendor Research Tool"
echo "======================================"

# 1. Check Python
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 not found. Install Python 3.11+"
  exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[OK] Python $PYTHON_VERSION"

# 2. Check/create virtual environment
if [ ! -d "venv" ]; then
  echo "[...] Creating virtual environment..."
  python3 -m venv venv
fi
source venv/bin/activate
echo "[OK] Virtual environment activated"

# 3. Install dependencies
echo "[...] Installing dependencies..."
pip install -q -r requirements.txt

# 4. Check .env file
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    cp .env.example .env
    echo "[WARN] Created .env from .env.example — edit it with your API keys!"
    echo "       Required: ANTHROPIC_API_KEY, TAVILY_API_KEY"
    exit 1
  else
    echo "ERROR: No .env file found. Create one with ANTHROPIC_API_KEY and TAVILY_API_KEY"
    exit 1
  fi
fi

# 5. Validate API keys are set
if grep -q "sk-ant-xxx" .env 2>/dev/null || grep -q "tvly-xxx" .env 2>/dev/null; then
  echo "[WARN] .env still has placeholder API keys — update them before running research"
fi

# 6. Run quality checks (optional, skip with --skip-checks)
if [[ "${1:-}" != "--skip-checks" ]]; then
  echo ""
  echo "--- Running Quality Checks ---"
  echo "[...] Linting..."
  python3 -m ruff check app/ tests/ --quiet && echo "[OK] Lint passed" || echo "[WARN] Lint issues found"
  echo "[...] Type checking..."
  python3 -m pyright app/ --warnings 2>/dev/null && echo "[OK] Types passed" || echo "[WARN] Type issues found"
  echo "[...] Running tests..."
  python3 -m pytest tests/ -q --tb=short && echo "[OK] Tests passed" || echo "[WARN] Some tests failed"
  echo "--- Quality Checks Done ---"
fi

# 7. Database status
echo ""
if [ -f "research.db" ]; then
  JOB_COUNT=$(python3 -c "
import sqlite3
conn = sqlite3.connect('research.db')
count = conn.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
print(count)
conn.close()
" 2>/dev/null || echo "0")
  echo "[OK] Database exists (research.db) — $JOB_COUNT previous job(s)"
  echo "     NOTE: No need to delete — schema is stable and auto-initialized"
else
  echo "[INFO] No database yet — will be created on first startup"
fi

# 8. Check if port 8000 is already in use
PORT=8000
if lsof -ti:$PORT &>/dev/null; then
  echo "[WARN] Port $PORT is already in use"
  PIDS=$(lsof -ti:$PORT)
  echo "       PIDs: $PIDS"
  read -rp "       Kill existing processes and continue? [Y/n] " REPLY
  REPLY=${REPLY:-Y}
  if [[ "$REPLY" =~ ^[Yy]$ ]]; then
    kill $PIDS 2>/dev/null || true
    sleep 1
    # Force kill if still running
    if lsof -ti:$PORT &>/dev/null; then
      kill -9 $(lsof -ti:$PORT) 2>/dev/null || true
      sleep 1
    fi
    echo "[OK] Port $PORT freed"
  else
    echo "       Aborting. Free port $PORT manually or use: kill \$(lsof -ti:$PORT)"
    exit 1
  fi
fi

# 9. Start the server (frontend is served at the same URL)
echo ""
echo "======================================"
echo "  Starting server..."
echo "  Backend API:  http://localhost:$PORT/api/"
echo "  Frontend UI:  http://localhost:$PORT/"
echo "  Health check: http://localhost:$PORT/health"
echo "======================================"
echo ""

python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port $PORT
