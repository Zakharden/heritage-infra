# heritage-infra

English overview: [README_EN.md](README_EN.md)

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

### 3. `heritage-k8s-helm-charts`

Helm chart-репозиторий для stateful-сервисов, которые раскатываются через Argo CD Applications.

Содержит:

- PostgreSQL chart (2 инстанса: `primary + replica`, по 2Gi RAM и 2Gi PVC);
- Redis chart (1 инстанс, standalone);
- HashiCorp Vault chart;
- Vault Secrets Operator + sync манифесты, чтобы пароли Postgres/Redis брались из Vault;
- готовые Argo CD `Application` manifests:
  - `heritage-k8s-helm-charts/argocd-applications/postgres-application.yaml`
  - `heritage-k8s-helm-charts/argocd-applications/redis-application.yaml`

Документация:
- `heritage-k8s-helm-charts/README.md`

Как раскатить Helm-чарты через Argo CD (app-of-apps):

1. Убедитесь, что Argo CD установлен (в `heritage-kubespray-automatic` он ставится автоматически, если включить опцию Argo CD).
2. Убедитесь, что Argo CD имеет доступ к git-репозиторию `heritage-infra` (репозиторий добавлен в Argo CD как `repoURL`).
3. Создайте “root” Application, который будет синхронизировать каталог `heritage-k8s-helm-charts/argocd-applications` (он содержит дочерние `Application` для Vault, Vault Secrets Operator, Vault Sync, Postgres, Redis):

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: heritage-helm-apps
  namespace: argocd
spec:
  project: default
  source:
    repoURL: git@github.com:Zakharden/heritage-infra.git
    targetRevision: HEAD  # default branch (после merge)
    path: heritage-k8s-helm-charts/argocd-applications
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

Далее Argo CD сам создаст и будет поддерживать дочерние приложения.

Важно:
- После того как `heritage-vault*` приложения станут `Synced/Healthy`, пароли **нужно положить в Vault вручную**. Инструкция находится в `heritage-k8s-helm-charts/README.md`.
- Wrapper-чарты вендорят зависимости Bitnami внутрь репозитория, чтобы Argo CD не зависел от доступа к Helm repo/index.

### Внешний доступ (Ingress / TCP)

В `heritage-k8s-helm-charts` есть отдельное Argo CD приложение:

- `heritage-k8s-helm-charts/argocd-applications/external-access-application.yaml`

Оно делает:

- Ingress для Vault UI/API: `vault.52.20.233.48.nip.io` (хост можно поменять в `heritage-k8s-helm-charts/external-access/vault-ingress.yaml`)
- TCP-прокси через `ingress-nginx` для:
  - PostgreSQL (primary): `NodePort 31432` -> `data/heritage-postgres-postgresql-primary:5432`
  - Redis: `NodePort 31379` -> `data/heritage-redis-master:6379`

Подключение с другого сервера (нужен доступ по сети к любому узлу кластера и открытые порты в SG/firewalld):

PostgreSQL:

```bash
psql -h <k8s_node_public_ip> -p 31432 -U app_user -d app_db
```

Redis:

```bash
redis-cli -h <k8s_node_public_ip> -p 31379 -a '<redis-password>'
```

Vault:

- UI/API: `http://vault.52.20.233.48.nip.io`
- логин: **token**
- root token (dev): `pass_heritage` (см. `heritage-k8s-helm-charts/vault/values.yaml`)

Где взять пароли:

```bash
# Postgres user password (app_user)
kubectl -n data get secret heritage-postgres-auth -o jsonpath='{.data.password}' | base64 -d; echo

# Redis password
kubectl -n data get secret heritage-redis-auth -o jsonpath='{.data.redis-password}' | base64 -d; echo
```

## Как это работает вместе

Порядок работы:

1. Подготавливаете VM через `ansible_host_settings`.
2. Раскатываете Kubernetes через `heritage-kubespray-automatic`.
3. Проверяете доступность кластера и addons (`kubectl get nodes`, `kubectl get storageclass`, `kubectl -n argocd get pods`).
4. Раскатываете stateful-сервисы (PostgreSQL/Redis/Vault) через Argo CD из `heritage-k8s-helm-charts`.

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

### Шаг 4. Раскатить PostgreSQL/Redis/Vault через Argo CD (Helm)

См. `heritage-k8s-helm-charts/README.md`:
- какие приложения создаются;
- в каком порядке они синхронизируются;
- как добавить секреты в Vault.

## Архитектурная роль репозитория

`heritage-infra` это единая точка входа для инфраструктурной команды:

- стандартизирует подготовку серверов;
- стандартизирует раскатку Kubernetes;
- хранит инфраструктурные решения в коде и git-истории;
- позволяет повторяемо поднимать новые окружения (dev/stage/prod) по одному шаблону.
