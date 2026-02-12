#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export ANSIBLE_CONFIG="${ROOT_DIR}/kubespray/ansible.cfg"
CLUSTER_NAME="${CLUSTER_NAME:-mycluster}"

ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --cluster)
      if [[ $# -lt 2 ]]; then
        echo "ERROR: --cluster requires a value." >&2
        exit 1
      fi
      CLUSTER_NAME="$2"
      shift 2
      ;;
    --cluster=*)
      CLUSTER_NAME="${1#*=}"
      shift
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done

INVENTORY_FILE="${ROOT_DIR}/inventory/${CLUSTER_NAME}/inventory.ini"
if [[ ! -f "${INVENTORY_FILE}" ]]; then
  echo "ERROR: Inventory not found: ${INVENTORY_FILE}" >&2
  exit 1
fi

if [[ -x "${ROOT_DIR}/.venv/bin/ansible-playbook" ]]; then
  ANSIBLE_PLAYBOOK="${ROOT_DIR}/.venv/bin/ansible-playbook"
else
  ANSIBLE_PLAYBOOK="ansible-playbook"
fi

"${ANSIBLE_PLAYBOOK}" \
  -i "${INVENTORY_FILE}" \
  "${ROOT_DIR}/kubespray/upgrade-cluster.yml" \
  "${ARGS[@]}"
