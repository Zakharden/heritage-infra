const hostsBody = document.getElementById("hosts-body");
const addHostBtn = document.getElementById("add-host");
const applyPresetBtn = document.getElementById("apply-preset");
const presetSelect = document.getElementById("preset-select");
const deployForm = document.getElementById("deploy-form");
const deployBtn = document.getElementById("deploy-btn");
const runStatus = document.getElementById("run-status");
const runCluster = document.getElementById("run-cluster");
const runLog = document.getElementById("run-log");

const PRESETS = {
  "aws-dev": {
    cluster_name: "heritage-dev",
    container_manager: "containerd",
    network_plugin: "cilium",
    storage_enabled: "true",
    argocd_enabled: "true",
    hosts: [
      {
        name: "vm-k8s-m1",
        ansible_host: "52.20.233.48",
        private_ip: "172.31.70.213",
        role_profile: "control_plane_etcd",
      },
      {
        name: "vm-k8s-w1",
        ansible_host: "34.194.182.115",
        private_ip: "172.31.17.45",
        role_profile: "worker",
      },
      {
        name: "vm-k8s-w2",
        ansible_host: "23.23.33.244",
        private_ip: "172.31.59.144",
        role_profile: "worker",
      },
    ],
  },
  "aws-ha": {
    cluster_name: "heritage-ha",
    container_manager: "containerd",
    network_plugin: "calico",
    storage_enabled: "true",
    argocd_enabled: "true",
    hosts: [
      {
        name: "cp-1",
        ansible_host: "10.0.1.11",
        private_ip: "10.0.1.11",
        role_profile: "control_plane_etcd",
      },
      {
        name: "cp-2",
        ansible_host: "10.0.1.12",
        private_ip: "10.0.1.12",
        role_profile: "control_plane_etcd",
      },
      {
        name: "cp-3",
        ansible_host: "10.0.1.13",
        private_ip: "10.0.1.13",
        role_profile: "control_plane_etcd",
      },
      {
        name: "w-1",
        ansible_host: "10.0.1.21",
        private_ip: "10.0.1.21",
        role_profile: "worker",
      },
      {
        name: "w-2",
        ansible_host: "10.0.1.22",
        private_ip: "10.0.1.22",
        role_profile: "worker",
      },
      {
        name: "w-3",
        ansible_host: "10.0.1.23",
        private_ip: "10.0.1.23",
        role_profile: "worker",
      },
    ],
  },
  "all-in-one": {
    cluster_name: "heritage-lab",
    container_manager: "containerd",
    network_plugin: "cilium",
    storage_enabled: "false",
    argocd_enabled: "false",
    hosts: [
      {
        name: "lab-1",
        ansible_host: "192.168.56.10",
        private_ip: "192.168.56.10",
        role_profile: "all",
      },
    ],
  },
};

function hostRowTemplate(host = {}) {
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td><input name="host_name[]" placeholder="vm-k8s-m1" value="${host.name || ""}" required /></td>
    <td><input name="host_ansible_host[]" placeholder="52.20.233.48" value="${host.ansible_host || ""}" required /></td>
    <td><input name="host_private_ip[]" placeholder="172.31.70.213" value="${host.private_ip || ""}" /></td>
    <td>
      <select name="host_role_profile[]">
        <option value="control_plane_etcd">control_plane_etcd</option>
        <option value="worker">worker</option>
        <option value="control_plane">control_plane</option>
        <option value="etcd">etcd</option>
        <option value="all">all</option>
      </select>
    </td>
    <td><button type="button" class="btn btn-danger remove-host">remove</button></td>
  `;
  tr.querySelector('select[name="host_role_profile[]"]').value =
    host.role_profile || "worker";

  tr.querySelector(".remove-host").addEventListener("click", () => {
    tr.remove();
    if (hostsBody.children.length === 0) {
      hostsBody.appendChild(hostRowTemplate());
    }
  });

  return tr;
}

function setField(name, value) {
  const element = deployForm.querySelector(`[name="${name}"]`);
  if (!element) return;
  if (element.type === "checkbox") {
    element.checked = value === true || value === "true";
  } else {
    element.value = value;
  }
}

function applyPreset(presetName) {
  const preset = PRESETS[presetName];
  if (!preset) return;
  setField("cluster_name", preset.cluster_name);
  setField("container_manager", preset.container_manager);
  setField("network_plugin", preset.network_plugin);
  setField("storage_enabled", preset.storage_enabled);
  setField("argocd_enabled", preset.argocd_enabled);

  hostsBody.innerHTML = "";
  preset.hosts.forEach((host) => {
    hostsBody.appendChild(hostRowTemplate(host));
  });
}

function setStatus(statusText) {
  runStatus.textContent = statusText;
  runStatus.classList.remove("running", "success", "failed");
  if (statusText === "running") runStatus.classList.add("running");
  if (statusText === "success") runStatus.classList.add("success");
  if (statusText === "failed") runStatus.classList.add("failed");
}

async function pollRun(runId) {
  if (!runId) return;
  try {
    const response = await fetch(`/api/run/${runId}`);
    const payload = await response.json();
    if (!response.ok || !payload.found) {
      setStatus("failed");
      runLog.textContent = payload.error || "Run not found";
      return;
    }

    setStatus(payload.status);
    runCluster.textContent = payload.cluster_name;
    runLog.textContent = payload.log_tail || "Ожидание вывода...";
    runLog.scrollTop = runLog.scrollHeight;

    if (payload.status === "running") {
      setTimeout(() => pollRun(runId), 2000);
    }
  } catch (error) {
    setStatus("failed");
    runLog.textContent = String(error);
  }
}

addHostBtn.addEventListener("click", () => {
  hostsBody.appendChild(hostRowTemplate());
});

applyPresetBtn.addEventListener("click", () => {
  applyPreset(presetSelect.value);
});

deployForm.addEventListener("submit", () => {
  deployBtn.disabled = true;
  deployBtn.textContent = "Запускаю...";
});

if (hostsBody.children.length === 0) {
  hostsBody.appendChild(hostRowTemplate());
}

const runId = document.body.dataset.runId || "";
const clusterName = document.body.dataset.clusterName || "";
if (clusterName) {
  runCluster.textContent = clusterName;
}

if (runId) {
  setStatus("running");
  pollRun(runId);
}
