# Подробный гайд по `heritage-kubespray-automatic`

## 1. Что это за репозиторий

`heritage-kubespray-automatic` это рабочая обертка над Kubespray (`v2.30.0`), где:

- сам Kubespray подключен как `git submodule` в папке `kubespray/`;
- настройки кластера лежат отдельно, в `inventory/<cluster_name>/`;
- есть скрипты для подготовки окружения, деплоя, апгрейда;
- есть UI, который генерирует inventory и запускает раскатку.

Главная идея: вы не меняете код Kubespray напрямую (по возможности), а управляете кластером через `inventory` и scripts/UI в этом репозитории.

---

## 2. Структура проекта

Ключевые директории и файлы:

- `kubespray/`
  - git submodule на официальный Kubespray.
  - Основной playbook кластера: `kubespray/playbooks/cluster.yml`.

- `inventory/mycluster/`
  - `inventory.ini` — список узлов и групп Ansible/Kubernetes.
  - `group_vars/all/all.yml` — общие параметры кластера.
  - `group_vars/k8s_cluster/k8s-cluster.yml` — сетка, runtime, kube-параметры.
  - `group_vars/k8s_cluster/addons.yml` — аддоны (storage, ingress, argocd и т.д.).
  - `credentials/` — секреты, генерируемые Kubespray (`kubeadm_certificate_key` и т.д.).
  - `manifests/argocd-ingress.yml` — ingress-ресурс для Argo CD.

- `scripts/`
  - `bootstrap.sh` — создание `.venv` и установка зависимостей.
  - `cluster-up.sh` — раскатка/обновление состояния кластера.
  - `cluster-upgrade.sh` — сценарий апгрейда кластера.
  - `ui.sh` — запуск Flask UI.

- `ui/`
  - `app.py` — backend UI: валидирует форму, генерирует inventory, запускает deploy.
  - `templates/index.html` — веб-форма.
  - `static/app.js` — клиентская логика (добавление хостов, пресеты, polling логов).
  - `runs/` — runtime-логи запусков UI.

---

## 3. Минимальные требования

- Linux/macOS хост с `bash`, `git`, `python3` (>= 3.10), `sudo`.
- SSH-доступ к нодам кластера.
- На нодах должен работать пакетный менеджер (для установки компонентов Kubespray).
- Сеть между нодами и доступ к интернету (или заранее подготовленный offline mirror).

Важно:

- `scripts/bootstrap.sh` проверяет версию Python и прерывает запуск, если версия ниже 3.10.
- Для AWS/VM обычно требуется открыть сетевые порты Kubernetes (API server, NodePort, overlay network).

---

## 4. Старт с нуля (короткий путь)

```bash
git clone git@github.com:Zakharden/heritage-infra.git
cd heritage-kubespray-automatic
git submodule update --init --recursive
./scripts/bootstrap.sh
./scripts/cluster-up.sh --cluster mycluster
```

После успешной раскатки `cluster-up.sh`:

- синхронизирует kubeconfig в `~/.kube/mycluster.conf`;
- по умолчанию обновляет `~/.kube/config`.

Проверка:

```bash
kubectl get nodes -o wide
kubectl get storageclass
kubectl -n argocd get pods
```

---

## 5. Как устроен `inventory.ini`

Файл: `inventory/mycluster/inventory.ini`

Пример логики:

- `[all]` — все хосты и их IP:
  - `ansible_host` — внешний IP/hostname для SSH;
  - `ip` — внутренний IP, который Kubernetes использует внутри кластера.
- `[kube_control_plane]` — control plane ноды.
- `[etcd]` — etcd ноды.
- `[kube_node]` — worker ноды.
- `[k8s_cluster:children]` — агрегатор групп.

Если у вас single-master:

- control-plane и etcd обычно одна и та же машина.

Если HA:

- минимум 3 control-plane+etcd узла (нечетное число для etcd кворума).

---

## 6. Где меняются параметры кластера

### 6.1 Общие параметры

Файл: `inventory/mycluster/group_vars/all/all.yml`

Сюда относятся прокси, DNS, NTP, параметры окружения и базовые настройки, общие для всех ролей.

### 6.2 Kubernetes core

Файл: `inventory/mycluster/group_vars/k8s_cluster/k8s-cluster.yml`

Ключевые поля:

- `kube_network_plugin` (`cilium`/`calico`);
- `container_manager` (`containerd`/`docker`);
- `cluster_name`, `dns_domain`, service/pod CIDR;
- `kubeconfig_localhost: true` и `kubeconfig_localhost_ansible_host: true`.

### 6.3 Аддоны

Файл: `inventory/mycluster/group_vars/k8s_cluster/addons.yml`

Текущие важные поля в вашем проекте:

- `local_path_provisioner_enabled: true`
- `local_volume_provisioner_enabled: true`
- `ingress_nginx_enabled: true`
- `argocd_enabled: true`

Также у нас задан NodePort ingress:

- `ingress_nginx_service_type: NodePort`
- `ingress_nginx_service_nodeport_http: 30080`
- `ingress_nginx_service_nodeport_https: 30443`

---

## 7. Скрипты и их поведение

### 7.1 `scripts/bootstrap.sh`

Что делает:

1. Определяет Python (`python3.11` или `python3`).
2. Проверяет версию Python >= 3.10.
3. Создает/переиспользует `.venv` в корне проекта.
4. Ставит зависимости:
   - `kubespray/requirements.txt`
   - `ui/requirements.txt`

### 7.2 `scripts/cluster-up.sh`

Что делает:

1. Берет inventory из `inventory/<cluster>/inventory.ini`.
2. Запускает `kubespray/cluster.yml` через Ansible.
3. Поддерживает retry (по умолчанию 2 попытки):
   - `CLUSTER_UP_MAX_ATTEMPTS`
   - `CLUSTER_UP_RETRY_DELAY_SECONDS`
4. После успеха пытается синхронизировать kubeconfig:
   - из `inventory/<cluster>/artifacts/admin.conf`
   - в `~/.kube/<cluster>.conf`
   - и (по умолчанию) в `~/.kube/config`

Полезные env-переменные:

- `CLUSTER_NAME=mycluster`
- `CLUSTER_UP_MAX_ATTEMPTS=3`
- `CLUSTER_UP_RETRY_DELAY_SECONDS=45`
- `CLUSTER_UP_SYNC_KUBECONFIG=true|false`
- `CLUSTER_UP_SET_DEFAULT_KUBECONFIG=true|false`

### 7.3 `scripts/cluster-upgrade.sh`

Использует `kubespray/upgrade-cluster.yml` с тем же inventory.

### 7.4 `scripts/ui.sh`

Запускает Flask UI (`ui/app.py`) на `HOST`/`PORT` (по умолчанию `0.0.0.0:8090`).

---

## 8. Работа через UI

Запуск:

```bash
./scripts/ui.sh
```

Открыть:

- `http://<ваш_хост>:8090`

Что вводите в UI:

- имя кластера;
- runtime;
- network plugin;
- storage on/off;
- argocd on/off;
- ansible user;
- ssh key;
- список хостов (name / ansible host / private ip / role profile).

Что UI делает в коде (`ui/app.py`):

1. Валидирует поля (`_normalize_cluster_name`, `_validate_choice`, `_collect_hosts`).
2. Копирует шаблон inventory из `inventory/mycluster` в новый `inventory/<cluster_name>`.
3. Генерирует `inventory/<cluster_name>/inventory.ini`.
4. Пишет overrides в:
   - `inventory/<cluster_name>/group_vars/k8s_cluster/zz-heritage-ui.yml`
5. Запускает:
   - `./scripts/cluster-up.sh --cluster <cluster_name>`

Логи каждого запуска UI:

- `ui/runs/<run_id>.log`

---

## 9. Storage в текущем проекте

### 9.1 `local-path` (dynamic provisioning)

Включается переменной:

- `local_path_provisioner_enabled: true`

Роль Kubespray:

- `kubespray/roles/kubernetes-apps/external_provisioner/local_path_provisioner/...`

Суть:

- создается provisioner `rancher.io/local-path`;
- создается StorageClass (обычно default) `local-path`;
- PV создаются динамически в локальном пути ноды.

### 9.2 `local-storage` (local volume provisioner)

Включается переменной:

- `local_volume_provisioner_enabled: true`

В нашем `addons.yml` задан storage class:

- имя: `local-storage`
- `host_dir`: `/mnt/disks`
- `mount_dir`: `/mnt/disks`

Важно понимать:

- этот класс использует `kubernetes.io/no-provisioner`;
- используется `WaitForFirstConsumer`;
- данные физически живут на диске конкретной ноды.

Проверка:

```bash
kubectl get storageclass
```

---

## 10. Ingress для Argo CD

### 10.1 Ingress Controller (Nginx)

Включен в:

- `inventory/mycluster/group_vars/k8s_cluster/addons.yml`

Сервис контроллера у вас NodePort:

- HTTP: `30080`
- HTTPS: `30443`

Проверка:

```bash
kubectl -n ingress-nginx get pods -o wide
kubectl -n ingress-nginx get svc ingress-nginx -o wide
```

### 10.2 Ingress-ресурс Argo CD

Файл:

- `inventory/mycluster/manifests/argocd-ingress.yml`

Что в нем:

- host: `argocd.52.20.233.48.nip.io`
- backend: `argocd/argocd-server:443`
- annotations для SSL passthrough.

Применение:

```bash
kubectl apply -f inventory/mycluster/manifests/argocd-ingress.yml
kubectl get ingress -A
```

Доступ:

- `https://argocd.52.20.233.48.nip.io:30443`

---

## 11. Argo CD: логин/пароль и базовые команды

Логин всегда:

- `admin`

Начальный пароль:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d && echo
```

Проверка подов:

```bash
kubectl -n argocd get pods -o wide
```

---

## 12. Частые сценарии

### 12.1 Раскатить только ingress-controller

```bash
./scripts/cluster-up.sh --cluster mycluster --tags ingress-controller
```

### 12.2 Раскатить только Argo CD

```bash
./scripts/cluster-up.sh --cluster mycluster --tags argocd
```

### 12.3 Обновить kubeconfig артефактами

```bash
./scripts/cluster-up.sh --cluster mycluster --tags client
```

### 12.4 Полная повторная идемпотентная прогонка

```bash
./scripts/cluster-up.sh --cluster mycluster
```

---

## 13. Диагностика проблем

### 13.1 `connection refused` к API server при аддонах

Что делать:

1. Повторить прогон (`cluster-up.sh` уже имеет retry).
2. Проверить здоровье control-plane:
   - `kubectl -n kube-system get pods -o wide`
   - `kubectl -n kube-system logs kube-apiserver-<node> -c kube-apiserver --previous`
3. Проверить kubelet:
   - `sudo journalctl -u kubelet -n 300 --no-pager`

### 13.2 `kubectl` ничего не показывает

Проверить:

```bash
kubectl config current-context
kubectl get nodes
ls -l ~/.kube/config
```

Если контекст/сертификаты не те:

- перезапустить `./scripts/cluster-up.sh --cluster mycluster --tags client`

### 13.3 Нет доступа к Argo CD снаружи

Проверить:

- открыт ли в Security Group порт `30443`;
- поды `ingress-nginx` в `Ready`;
- Ingress существует (`kubectl get ingress -A`).

---

## 14. Рекомендуемый рабочий цикл

1. Меняете параметры в `inventory/.../group_vars/...`.
2. Прогоняете `./scripts/cluster-up.sh --cluster <name>`.
3. Проверяете:
   - `kubectl get nodes`
   - `kubectl get storageclass`
   - `kubectl -n argocd get pods`
4. Фиксируете изменения в git.
5. Отправляете в удаленный репозиторий.

