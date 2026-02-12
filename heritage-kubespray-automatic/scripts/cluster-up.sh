#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export ANSIBLE_CONFIG="${ROOT_DIR}/kubespray/ansible.cfg"
CLUSTER_NAME="${CLUSTER_NAME:-mycluster}"
MAX_ATTEMPTS="${CLUSTER_UP_MAX_ATTEMPTS:-2}"
RETRY_DELAY_SECONDS="${CLUSTER_UP_RETRY_DELAY_SECONDS:-30}"

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
ARTIFACT_KUBECONFIG="${ROOT_DIR}/inventory/${CLUSTER_NAME}/artifacts/admin.conf"
if [[ ! -f "${INVENTORY_FILE}" ]]; then
  echo "ERROR: Inventory not found: ${INVENTORY_FILE}" >&2
  exit 1
fi

if [[ -x "${ROOT_DIR}/.venv/bin/ansible-playbook" ]]; then
  ANSIBLE_PLAYBOOK="${ROOT_DIR}/.venv/bin/ansible-playbook"
else
  ANSIBLE_PLAYBOOK="ansible-playbook"
fi

if [[ ! "${MAX_ATTEMPTS}" =~ ^[1-9][0-9]*$ ]]; then
  echo "ERROR: CLUSTER_UP_MAX_ATTEMPTS must be a positive integer. Current value: ${MAX_ATTEMPTS}" >&2
  exit 1
fi

if [[ ! "${RETRY_DELAY_SECONDS}" =~ ^[0-9]+$ ]]; then
  echo "ERROR: CLUSTER_UP_RETRY_DELAY_SECONDS must be a non-negative integer. Current value: ${RETRY_DELAY_SECONDS}" >&2
  exit 1
fi

is_true() {
  case "${1,,}" in
    1|true|yes|on)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

copy_with_optional_sudo() {
  local src="$1"
  local dst="$2"

  if [[ -r "${src}" ]]; then
    cp "${src}" "${dst}"
    return 0
  fi

  if command -v sudo >/dev/null 2>&1 && sudo -n test -r "${src}" >/dev/null 2>&1; then
    sudo cp "${src}" "${dst}"
    sudo chown "$(id -u)":"$(id -g)" "${dst}"
    return 0
  fi

  return 1
}

file_exists_with_optional_sudo() {
  local path="$1"

  if [[ -f "${path}" ]]; then
    return 0
  fi

  if command -v sudo >/dev/null 2>&1 && sudo -n test -f "${path}" >/dev/null 2>&1; then
    return 0
  fi

  return 1
}

attempt=1
last_rc=0
while (( attempt <= MAX_ATTEMPTS )); do
  echo "INFO: Deploy attempt ${attempt}/${MAX_ATTEMPTS} for cluster '${CLUSTER_NAME}'."
  if "${ANSIBLE_PLAYBOOK}" \
    -i "${INVENTORY_FILE}" \
    "${ROOT_DIR}/kubespray/cluster.yml" \
    "${ARGS[@]}"; then
    last_rc=0
    break
  fi

  last_rc=$?
  if (( attempt == MAX_ATTEMPTS )); then
    break
  fi

  echo "WARN: Deploy failed with rc=${last_rc}. Retrying in ${RETRY_DELAY_SECONDS}s..." >&2
  sleep "${RETRY_DELAY_SECONDS}"
  attempt=$((attempt + 1))
done

if (( last_rc != 0 )); then
  echo "ERROR: Cluster deployment failed after ${MAX_ATTEMPTS} attempt(s)." >&2
  exit "${last_rc}"
fi

if is_true "${CLUSTER_UP_SYNC_KUBECONFIG:-true}"; then
  if file_exists_with_optional_sudo "${ARTIFACT_KUBECONFIG}"; then
    KUBE_DIR="${HOME}/.kube"
    NAMED_KUBECONFIG="${KUBE_DIR}/${CLUSTER_NAME}.conf"
    DEFAULT_KUBECONFIG="${KUBE_DIR}/config"

    mkdir -p "${KUBE_DIR}"
    if ! copy_with_optional_sudo "${ARTIFACT_KUBECONFIG}" "${NAMED_KUBECONFIG}"; then
      echo "WARN: kubeconfig artifact exists but is not readable: ${ARTIFACT_KUBECONFIG}" >&2
      echo "WARN: Run with sudo rights or fix permissions, then re-run cluster-up.sh." >&2
      exit 1
    fi
    chmod 600 "${NAMED_KUBECONFIG}"

    if is_true "${CLUSTER_UP_SET_DEFAULT_KUBECONFIG:-true}"; then
      cp "${NAMED_KUBECONFIG}" "${DEFAULT_KUBECONFIG}"
      chmod 600 "${DEFAULT_KUBECONFIG}"
      echo "INFO: kubeconfig updated: ${DEFAULT_KUBECONFIG}"
    else
      echo "INFO: kubeconfig saved: ${NAMED_KUBECONFIG}"
      echo "INFO: export KUBECONFIG=${NAMED_KUBECONFIG}"
    fi
  else
    echo "WARN: kubeconfig artifact not found at ${ARTIFACT_KUBECONFIG}." >&2
    echo "WARN: Enable kubeconfig_localhost: true in inventory group_vars to auto-generate it." >&2
  fi
fi
