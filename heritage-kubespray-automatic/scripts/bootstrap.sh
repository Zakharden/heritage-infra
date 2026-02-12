#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN="python3.11"
else
  PYTHON_BIN="python3"
fi

PYTHON_VERSION="$("${PYTHON_BIN}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if ! "${PYTHON_BIN}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
  echo "ERROR: Kubespray v2.30.0 requires Python >= 3.10. Found ${PYTHON_VERSION} (${PYTHON_BIN})." >&2
  exit 1
fi

if [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  VENV_VERSION="$("${ROOT_DIR}/.venv/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  if [[ "${VENV_VERSION}" != "${PYTHON_VERSION}" ]]; then
    "${PYTHON_BIN}" -m venv --clear "${ROOT_DIR}/.venv"
  fi
else
  "${PYTHON_BIN}" -m venv "${ROOT_DIR}/.venv"
fi

source "${ROOT_DIR}/.venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "${ROOT_DIR}/kubespray/requirements.txt"
python -m pip install -r "${ROOT_DIR}/ui/requirements.txt"
