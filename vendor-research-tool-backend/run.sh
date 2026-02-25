#!/usr/bin/env bash
set -euo pipefail

# ─── SignalCore Vendor Research Tool — Backend Run Script ───

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$PROJECT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

echo "======================================"
echo "  SignalCore Vendor Research Tool"
echo "  Backend Server"
echo "======================================"

# 1. Check Python
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 not found. Install Python 3.11+"
  exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[OK] Python $PYTHON_VERSION"

# 2. Check/create virtual environment (at repo root)
VENV_DIR="$REPO_ROOT/venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "[...] Creating virtual environment at $VENV_DIR..."
  python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
echo "[OK] Virtual environment activated"

# 3. Install dependencies
echo "[...] Installing dependencies..."
pip install -q -r requirements.txt

# 4. Check .env file
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    cp .env.example .env
    echo "[WARN] Created .env from .env.example — edit it with your API keys!"
    echo "       Required: TAVILY_API_KEY + one LLM provider key"
    exit 1
  else
    echo "ERROR: No .env file found. Create one from .env.example"
    exit 1
  fi
fi

# 5. Validate API keys for the selected provider
LLM_PROVIDER=$(grep -E "^LLM_PROVIDER=" .env 2>/dev/null | cut -d= -f2 | tr -d ' "'"'" || echo "openrouter")
LLM_PROVIDER=${LLM_PROVIDER:-openrouter}

case "$LLM_PROVIDER" in
  openrouter)
    if grep -qE "^OPENROUTER_API_KEY=(sk-or-xxx|)$" .env 2>/dev/null; then
      echo "[WARN] OPENROUTER_API_KEY not set — required for LLM_PROVIDER=openrouter"
    fi
    ;;
  anthropic)
    if grep -qE "^ANTHROPIC_API_KEY=(sk-ant-xxx|)$" .env 2>/dev/null; then
      echo "[WARN] ANTHROPIC_API_KEY not set — required for LLM_PROVIDER=anthropic"
    fi
    ;;
  openai)
    if grep -qE "^OPENAI_API_KEY=(sk-xxx|)$" .env 2>/dev/null; then
      echo "[WARN] OPENAI_API_KEY not set — required for LLM_PROVIDER=openai"
    fi
    ;;
esac

if grep -qE "^TAVILY_API_KEY=(tvly-xxx|)$" .env 2>/dev/null; then
  echo "[WARN] TAVILY_API_KEY not set — required for web search"
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
mkdir -p data
if [ -f "data/research.db" ]; then
  JOB_COUNT=$(python3 -c "
import sqlite3
conn = sqlite3.connect('data/research.db')
count = conn.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
print(count)
conn.close()
" 2>/dev/null || echo "0")
  echo "[OK] Database exists (data/research.db) — $JOB_COUNT previous job(s)"
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

# 9. Start the backend API server
echo ""
echo "======================================"
echo "  Starting backend server..."
echo "  Backend API:  http://localhost:$PORT/api/"
echo "  Health check: http://localhost:$PORT/health"
echo "  Frontend:     cd ../vendor-research-tool-frontend && npm run dev"
echo "======================================"
echo ""

python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port $PORT
