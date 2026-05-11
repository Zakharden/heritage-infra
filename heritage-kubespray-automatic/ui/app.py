#!/usr/bin/env python3
from __future__ import annotations

import re
import shutil
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import yaml
from flask import Flask, jsonify, redirect, render_template, request, url_for

ROOT_DIR = Path(__file__).resolve().parents[1]
INVENTORY_ROOT = ROOT_DIR / "inventory"
BASE_CLUSTER = "mycluster"
RUNS_DIR = ROOT_DIR / "ui" / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)

APP = Flask(
    __name__,
    static_folder=str((ROOT_DIR / "ui" / "static")),
    template_folder=str((ROOT_DIR / "ui" / "templates")),
)
APP.secret_key = "heritage-kubespray-automatic-ui"

RUNS: Dict[str, Dict[str, object]] = {}
RUNS_LOCK = threading.Lock()

CLUSTER_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
HOST_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,62}$")


@dataclass
class HostEntry:
    name: str
    ansible_host: str
    private_ip: str
    role_profile: str


def _normalize_cluster_name(raw_value: str) -> str:
    cluster_name = raw_value.strip().lower()
    if not CLUSTER_NAME_RE.fullmatch(cluster_name):
        raise ValueError(
            "Имя кластера должно быть в формате [a-z0-9-], 2-63 символа."
        )
    return cluster_name


def _validate_choice(value: str, allowed: List[str], field_name: str) -> str:
    if value not in allowed:
        raise ValueError(f"Некорректный выбор для {field_name}: {value}")
    return value


def _to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _collect_hosts() -> List[HostEntry]:
    names = request.form.getlist("host_name[]")
    ansible_hosts = request.form.getlist("host_ansible_host[]")
    private_ips = request.form.getlist("host_private_ip[]")
    role_profiles = request.form.getlist("host_role_profile[]")

    max_len = max(len(names), len(ansible_hosts), len(private_ips), len(role_profiles))
    hosts: List[HostEntry] = []
    seen_names = set()

    for idx in range(max_len):
        name = (names[idx] if idx < len(names) else "").strip()
        ansible_host = (ansible_hosts[idx] if idx < len(ansible_hosts) else "").strip()
        private_ip = (private_ips[idx] if idx < len(private_ips) else "").strip()
        role_profile = (
            role_profiles[idx] if idx < len(role_profiles) else "worker"
        ).strip()

        if not name and not ansible_host and not private_ip:
            continue

        if not name:
            raise ValueError(f"Хост #{idx + 1}: укажите имя.")
        if not ansible_host:
            raise ValueError(f"Хост #{idx + 1}: укажите ansible_host.")
        if not HOST_NAME_RE.fullmatch(name):
            raise ValueError(
                f"Хост #{idx + 1}: имя '{name}' должно быть в формате [a-zA-Z0-9._-]."
            )
        if name in seen_names:
            raise ValueError(f"Имя хоста '{name}' дублируется.")

        role_profile = _validate_choice(
            role_profile,
            ["control_plane_etcd", "control_plane", "worker", "etcd", "all"],
            f"роль хоста {name}",
        )

        seen_names.add(name)
        hosts.append(
            HostEntry(
                name=name,
                ansible_host=ansible_host,
                private_ip=private_ip or ansible_host,
                role_profile=role_profile,
            )
        )

    if not hosts:
        raise ValueError("Добавьте минимум один хост.")
    return hosts


def _copy_cluster_skeleton(target_cluster: str) -> Path:
    source_dir = INVENTORY_ROOT / BASE_CLUSTER
    target_dir = INVENTORY_ROOT / target_cluster
    created_now = False

    if not source_dir.exists():
        raise RuntimeError(f"Шаблон inventory не найден: {source_dir}")

    if not target_dir.exists():
        shutil.copytree(source_dir, target_dir)
        created_now = True

    (target_dir / "credentials").mkdir(parents=True, exist_ok=True)
    if created_now:
        for item in (target_dir / "credentials").iterdir():
            if item.name == ".gitkeep":
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    gitkeep = target_dir / "credentials" / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()

    (target_dir / "group_vars" / "k8s_cluster").mkdir(parents=True, exist_ok=True)
    return target_dir


def _build_group_lists(hosts: List[HostEntry]) -> Tuple[List[str], List[str], List[str]]:
    kube_control_plane: List[str] = []
    etcd: List[str] = []
    kube_node: List[str] = []

    for host in hosts:
        role = host.role_profile
        if role in {"control_plane_etcd", "control_plane", "all"}:
            kube_control_plane.append(host.name)
        if role in {"control_plane_etcd", "etcd", "all"}:
            etcd.append(host.name)
        if role in {"worker", "all"}:
            kube_node.append(host.name)

    if not kube_control_plane:
        raise ValueError("Нужен минимум один control-plane хост.")
    if not etcd:
        etcd = list(kube_control_plane)
    if not kube_node:
        kube_node = list(kube_control_plane)

    return kube_control_plane, etcd, kube_node


def _write_inventory_ini(
    inventory_dir: Path,
    hosts: List[HostEntry],
    ansible_user: str,
    ansible_ssh_key: str,
    ansible_become: bool,
) -> None:
    kube_control_plane, etcd, kube_node = _build_group_lists(hosts)

    lines: List[str] = ["[all]"]
    for host in hosts:
        lines.append(
            f"{host.name} ansible_host={host.ansible_host} ip={host.private_ip}"
        )

    lines.extend(["", "[all:vars]"])
    lines.append(f"ansible_user={ansible_user}")
    lines.append(f"ansible_become={'true' if ansible_become else 'false'}")
    if ansible_become:
        lines.append("ansible_become_method=sudo")
    lines.append(f"ansible_ssh_private_key_file={ansible_ssh_key}")

    lines.extend(["", "[kube_control_plane]"])
    lines.extend(kube_control_plane)
    lines.extend(["", "[etcd]"])
    lines.extend(etcd)
    lines.extend(["", "[kube_node]"])
    lines.extend(kube_node)

    lines.extend(
        [
            "",
            "[calico_rr]",
            "",
            "[k8s_cluster:children]",
            "kube_control_plane",
            "kube_node",
            "calico_rr",
            "",
            "[bastion]",
            "",
        ]
    )

    inventory_file = inventory_dir / "inventory.ini"
    inventory_file.write_text("\n".join(lines), encoding="utf-8")


def _write_ui_overrides(
    inventory_dir: Path,
    cluster_name: str,
    container_manager: str,
    network_plugin: str,
    storage_enabled: bool,
    argocd_enabled: bool,
) -> None:
    overrides = {
        "cluster_name": f"{cluster_name}.local",
        "container_manager": container_manager,
        "kube_network_plugin": network_plugin,
        "persistent_volumes_enabled": storage_enabled,
        "local_path_provisioner_enabled": storage_enabled,
        "local_volume_provisioner_enabled": storage_enabled,
        "argocd_enabled": argocd_enabled,
        "argocd_namespace": "argocd",
    }

    if storage_enabled:
        overrides["local_volume_provisioner_nodelabels"] = ["kubernetes.io/hostname"]
        overrides["local_volume_provisioner_storage_classes"] = {
            "local-storage": {
                "host_dir": "/mnt/disks",
                "mount_dir": "/mnt/disks",
                "volume_mode": "Filesystem",
                "fs_type": "ext4",
                "reclaim_policy": "Delete",
            }
        }

    overrides_file = inventory_dir / "group_vars" / "k8s_cluster" / "zz-heritage-ui.yml"
    payload = "# Managed by heritage-kubespray-automatic UI\n" + yaml.safe_dump(
        overrides, sort_keys=False
    )
    overrides_file.write_text(payload, encoding="utf-8")


def _prepare_inventory() -> str:
    cluster_name = _normalize_cluster_name(request.form.get("cluster_name", ""))
    container_manager = _validate_choice(
        request.form.get("container_manager", "containerd"),
        ["containerd", "docker"],
        "runtime",
    )
    network_plugin = _validate_choice(
        request.form.get("network_plugin", "cilium"),
        ["cilium", "calico"],
        "network plugin",
    )
    storage_enabled = _to_bool(request.form.get("storage_enabled", "true"))
    argocd_enabled = _to_bool(request.form.get("argocd_enabled", "true"))
    ansible_become = _to_bool(request.form.get("ansible_become", "true"))

    ansible_user = request.form.get("ansible_user", "ec2-user").strip() or "ec2-user"
    ansible_ssh_key = (
        request.form.get("ansible_ssh_private_key_file", "~/.ssh/id_rsa").strip()
        or "~/.ssh/id_rsa"
    )

    hosts = _collect_hosts()
    inventory_dir = _copy_cluster_skeleton(cluster_name)
    _write_inventory_ini(
        inventory_dir=inventory_dir,
        hosts=hosts,
        ansible_user=ansible_user,
        ansible_ssh_key=ansible_ssh_key,
        ansible_become=ansible_become,
    )
    _write_ui_overrides(
        inventory_dir=inventory_dir,
        cluster_name=cluster_name,
        container_manager=container_manager,
        network_plugin=network_plugin,
        storage_enabled=storage_enabled,
        argocd_enabled=argocd_enabled,
    )
    return cluster_name


def _start_cluster_deploy(cluster_name: str) -> str:
    run_id = uuid.uuid4().hex[:8]
    log_path = RUNS_DIR / f"{run_id}.log"
    command = [str(ROOT_DIR / "scripts" / "cluster-up.sh"), "--cluster", cluster_name]

    with log_path.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            command,
            cwd=ROOT_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )

    with RUNS_LOCK:
        RUNS[run_id] = {
            "process": process,
            "cluster_name": cluster_name,
            "command": command,
            "created_at": int(time.time()),
            "log_path": str(log_path),
        }
    return run_id


def _read_tail(log_path: Path, max_lines: int = 300) -> str:
    if not log_path.exists():
        return ""
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-max_lines:])


@APP.get("/")
def index():
    return render_template(
        "index.html",
        run_id=request.args.get("run_id", ""),
        cluster_name=request.args.get("cluster_name", ""),
        error=request.args.get("error", ""),
    )


@APP.post("/deploy")
def deploy():
    try:
        cluster_name = _prepare_inventory()
        run_id = _start_cluster_deploy(cluster_name)
        return redirect(
            url_for("index", run_id=run_id, cluster_name=cluster_name, error="")
        )
    except Exception as exc:  # noqa: BLE001
        return redirect(url_for("index", error=str(exc)))


@APP.get("/api/run/<run_id>")
def run_state(run_id: str):
    with RUNS_LOCK:
        run_data = RUNS.get(run_id)

    if not run_data:
        return jsonify({"found": False, "error": "Run not found"}), 404

    process: subprocess.Popen = run_data["process"]  # type: ignore[assignment]
    return_code = process.poll()
    status = "running" if return_code is None else "success" if return_code == 0 else "failed"
    log_path = Path(str(run_data["log_path"]))

    return jsonify(
        {
            "found": True,
            "run_id": run_id,
            "cluster_name": run_data["cluster_name"],
            "created_at": run_data["created_at"],
            "status": status,
            "return_code": return_code,
            "log_tail": _read_tail(log_path),
            "command": run_data["command"],
        }
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="heritage-kubespray-automatic UI")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8090)
    args = parser.parse_args()
    APP.run(host=args.host, port=args.port, debug=False)
