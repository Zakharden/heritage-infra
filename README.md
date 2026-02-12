# heritage-infra

Инфраструктурный репозиторий для HSE start-up.  
Содержит полный pipeline: от подготовки чистых VM до автоматической раскатки Kubernetes-кластера.

## Что внутри

### 1. `ansible_host_settings`

Набор Ansible playbooks для базовой подготовки виртуальных машин под Kubernetes.

Что делает:

1. На **всех** узлах:
   - установка базовых пакетов;
   - создание пользователя `viewer` без root/sudo прав;
   - настройка времени (`chronyd`, timezone);
   - отключение swap (текущее + `/etc/fstab`);
   - настройка sysctl и модулей ядра для Kubernetes;
   - установка и настройка `containerd` (`SystemdCgroup=true`);
   - установка `kubelet`, `kubeadm`, `kubectl`, `cri-tools`;
   - создание рабочих директорий (`/var/lib/kubelet`, `/var/lib/containerd`, `/var/log/kubernetes`, `/opt/k8s/bin`, `/data`);
   - ограничение размера systemd-journald под диск 40 GB;
   - авторасширение корневого раздела (если автоматически определяется схема диска);
   - открытие базовых портов Kubernetes в `firewalld`.

2. Только на **master**:
   - установка `python3.11` и `python3.11-pip`;
   - проверка установленной версии Python 3.11.

Полная документация:
- `ansible_host_settings/README.md`

### 2. `heritage-kubespray-automatic`

Репозиторий для автоматической раскатки и сопровождения Kubernetes через Kubespray (`v2.30.0`).

Что включает:

- `inventory` и `group_vars` для ваших кластеров;
- `kubespray/` как git submodule;
- скрипты для деплоя и апгрейда (`cluster-up.sh`, `cluster-upgrade.sh`);
- web UI для генерации inventory и запуска раскатки;
- автоматическую установку ключевых addons (storage, ingress, Argo CD).

Основной функционал:

- раскатка кластера одной командой;
- retry при временной нестабильности API в процессе deploy;
- синхронизация kubeconfig после успешной раскатки;
- включенные storage classes:
  - `local-path`
  - `local-storage`
- автоматическая установка Argo CD;
- раскатка ingress-nginx и Ingress для Argo CD.

Полная документация:
- `heritage-kubespray-automatic/README.md`
- `heritage-kubespray-automatic/docs/OPERATIONS_GUIDE_RU.md`
- `heritage-kubespray-automatic/docs/LEARNING_CLUSTER_FROM_ZERO_RU.md`

Скриншот UI:

![heritage-kubespray-automatic UI](heritage-kubespray-automatic/docs/images/ui-screenshot.png)

## Как это работает вместе

Порядок работы:

1. Подготавливаете VM через `ansible_host_settings`.
2. Раскатываете Kubernetes через `heritage-kubespray-automatic`.
3. Проверяете доступность кластера и addons (`kubectl get nodes`, `kubectl get storageclass`, `kubectl -n argocd get pods`).

Идея проста:

- `ansible_host_settings` отвечает за готовность ОС и runtime;
- `heritage-kubespray-automatic` отвечает за сам Kubernetes и его приложения.

## Быстрый старт

### Шаг 1. Подготовить хосты

```bash
cd ansible_host_settings
chmod +x scripts/bootstrap_env.sh
./scripts/bootstrap_env.sh
./.venv/bin/ansible-playbook -i inventory/hosts.ini playbooks/site.yml
```

### Шаг 2. Раскатить кластер

```bash
cd ../heritage-kubespray-automatic
git submodule update --init --recursive
./scripts/bootstrap.sh
./scripts/cluster-up.sh --cluster mycluster
```

### Шаг 3. Проверить результат

```bash
kubectl get nodes -o wide
kubectl get storageclass
kubectl -n argocd get pods
```

## Архитектурная роль репозитория

`heritage-infra` это единая точка входа для инфраструктурной команды:

- стандартизирует подготовку серверов;
- стандартизирует раскатку Kubernetes;
- хранит инфраструктурные решения в коде и git-истории;
- позволяет повторяемо поднимать новые окружения (dev/stage/prod) по одному шаблону.
