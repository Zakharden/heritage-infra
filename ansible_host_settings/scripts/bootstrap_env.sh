#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "ERROR: Python binary '$PYTHON_BIN' not found."
  echo "Set another interpreter: PYTHON_BIN=python3.11 ./scripts/bootstrap_env.sh"
  exit 1
fi

echo "[1/4] Creating virtual environment: $VENV_DIR"
"$PYTHON_BIN" -m venv "$VENV_DIR"

echo "[2/4] Upgrading pip/setuptools/wheel"
"$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel

echo "[3/4] Installing python dependencies from requirements.txt"
"$VENV_DIR/bin/pip" install -r "$ROOT_DIR/requirements.txt"

echo "[4/4] Verifying ansible installation"
"$VENV_DIR/bin/ansible-playbook" --version

cat <<EOF

Environment is ready.

Use one of the following:
  source "$VENV_DIR/bin/activate"
  $VENV_DIR/bin/ansible-playbook -i inventory/hosts.ini playbooks/site.yml

EOF
