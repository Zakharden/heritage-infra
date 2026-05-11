#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8090}"

if [[ ! -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  echo "ERROR: venv is not initialized. Run ./scripts/bootstrap.sh first." >&2
  exit 1
fi

source "${ROOT_DIR}/.venv/bin/activate"
python "${ROOT_DIR}/ui/app.py" --host "${HOST}" --port "${PORT}"
