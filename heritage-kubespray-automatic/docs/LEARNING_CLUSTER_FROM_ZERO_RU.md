# Обучающая статья: как с нуля раскатывается кластер в `heritage-kubespray-automatic`

## Введение

Если вы абсолютный новичок, главное понять одну мысль:

- вы **не ставите Kubernetes вручную по командам**;
- вы **описываете желаемое состояние** в inventory и переменных;
- Kubespray + Ansible приводят инфраструктуру к этому состоянию.

Этот репозиторий специально сделан так, чтобы управление шло через понятные файлы и скрипты.

---

## 1. Базовые понятия перед стартом

### 1.1 Что такое control plane

Control plane это «мозг» Kubernetes:

- `kube-apiserver` — API, через который работает весь кластер;
- `kube-controller-manager` — контроллеры (следят, чтобы текущее состояние совпадало с желаемым);
- `kube-scheduler` — решает, на какой ноде запускать Pod;
- `etcd` — база данных состояния кластера.

### 1.2 Что такое worker node

Worker — это узел, где запускаются ваши приложения (Pods). Там работают:

- `kubelet`;
- `kube-proxy`;
- контейнерный runtime (`containerd` или `docker`) - в моём случае containerd.

### 1.3 Почему есть `inventory.ini`

`inventory.ini` отвечает на вопрос:

- какие машины участвуют;
- какие у них роли;
- как до них подключаться по SSH.

Информация для работы Ansible.

---

## 2. С чего реально начинается раскатка

### Шаг 1. Подготовка репозитория

Вы делаете:

```bash
git clone git@github.com:Zakharden/heritage-infra.git
cd heritage-kubespray-automatic
git submodule update --init --recursive
./scripts/bootstrap.sh
```

Что делает `bootstrap.sh`:

1. Проверяет Python >= 3.10.
2. Создает виртуальное окружение `.venv`.
3. Ставит зависимости Ansible/Kubespray/UI.

Без этого дальше раскатка часто падает на missing dependencies.

### Шаг 2. Описание кластера в inventory

Файл: `inventory/mycluster/inventory.ini`

Вы описываете:

- control-plane хост(ы);
- etcd хост(ы);
- worker хост(ы);
- SSH пользователя и ключ.

### Шаг 3. Настройка поведения кластера

Файлы:

- `inventory/mycluster/group_vars/all/all.yml`
- `inventory/mycluster/group_vars/k8s_cluster/k8s-cluster.yml`
- `inventory/mycluster/group_vars/k8s_cluster/addons.yml`

Именно там вы выбираете runtime, CNI, storage, ingress, Argo CD и т.д.

### Шаг 4. Запуск раскатки

```bash
./scripts/cluster-up.sh --cluster mycluster
```

Этот скрипт запускает `kubespray/cluster.yml`.

---

## 3. Что происходит по порядку внутри Kubespray

Ниже порядок взят из файла `kubespray/playbooks/cluster.yml`.

### Этап 0. Prechecks и facts

До основной установки Kubespray:

- валидирует inventory;
- собирает факты о серверах;
- проверяет совместимость параметров.

Зачем это нужно:

- лучше упасть сразу на неверной конфигурации, чем в середине установки :)

Помним, что:
- Неважно, сколько раз ты упал, важно, сколько раз ты поднялся!

### Этап 1. Prepare for etcd install

Роли, которые идут перед etcd:

- `kubernetes/preinstall`
- `container-engine`
- `download`

Что делается:

- базовая подготовка ОС;
- установка runtime;
- скачивание бинарников/образов.

### Этап 2. Install etcd

Создается/настраивается etcd-кластер.

Почему это раньше control plane:

- API server хранит все состояние в etcd;
- без etcd control plane не имеет «источника правды».

### Этап 3. Install Kubernetes nodes

Ставятся node-компоненты на все узлы кластера.

### Этап 4. Install the control plane

На узлах control-plane настраиваются:

- API server;
- scheduler;
- controller-manager;
- клиентская конфигурация (`kubernetes/client`).

Здесь же у вас формируется `admin.conf`, который потом копируется в `inventory/<cluster>/artifacts/admin.conf` (если включен `kubeconfig_localhost`).

### Этап 5. kubeadm + CNI

Плей:

- `kubernetes/kubeadm`
- `network_plugin`

Что это значит:

- узлы join-ятся в кластер;
- устанавливается CNI (`calico` или `cilium`).

Почему это критично:

- пока нет CNI, Pod-сеть не работает полноценно.

### Этап 6. Kubernetes apps (аддоны)

Этот этап включает:

- ingress controller;
- external provisioner (storage);
- и другие приложения (в т.ч. Argo CD).

Порядок внутри ваших аддонов важен: сначала база кластера и сеть, потом прикладные компоненты.

---

## 4. Почему именно такой порядок

Коротко:

1. Нельзя ставить прикладные аддоны, пока нет стабильного API server.
2. Нельзя стабильно запускать Pod-аддоны без CNI.
3. Нельзя хранить кластерное состояние без etcd.

То есть порядок отражает зависимости:

- `OS/runtime -> etcd -> control-plane -> kubeadm/join -> CNI -> addons`.

---

## 5. Как создается local storage

В этом кластере включены оба варианта local storage, но они решают немного разные задачи.

## 5.1 `local-path-provisioner` (dynamic local path)

Где включается:

- `inventory/mycluster/group_vars/k8s_cluster/addons.yml`
  - `local_path_provisioner_enabled: true`

Где код роли:

- `kubespray/roles/kubernetes-apps/external_provisioner/local_path_provisioner/tasks/main.yml`
- `kubespray/roles/kubernetes-apps/external_provisioner/local_path_provisioner/templates/*.j2`

Что делает роль:

1. Создает namespace.
2. Создает service account/role/binding.
3. Создает deployment provisioner.
4. Создает StorageClass `local-path`.

Как работает:

- при создании PVC под этот класс provisioner создает PV динамически в локальной файловой системе ноды.

## 5.2 `local-volume-provisioner` (node-local volumes)

Где включается:

- `inventory/mycluster/group_vars/k8s_cluster/addons.yml`
  - `local_volume_provisioner_enabled: true`

Где код роли:

- `kubespray/roles/kubernetes-apps/external_provisioner/local_volume_provisioner/tasks/main.yml`
- `kubespray/roles/kubernetes-apps/external_provisioner/local_volume_provisioner/tasks/basedirs.yml`
- `kubespray/roles/kubernetes-apps/external_provisioner/local_volume_provisioner/templates/local-volume-provisioner-sc.yml.j2`

Что делает роль:

1. Проходит по всем нодам и storage class ключам.
2. На каждой ноде создает базовый путь (`/mnt/disks` у меня).
3. Рендерит манифесты provisioner.
4. Применяет их в кластере.
5. Создает StorageClass `local-storage` с `kubernetes.io/no-provisioner`.

Почему `WaitForFirstConsumer`:

- Kubernetes откладывает финальную привязку PV до момента, когда известно, на какую ноду пойдет Pod.
- Это снижает риск «PV на ноде A, Pod запланирован на ноду B».

Важный practical момент:

- local-storage не реплицирует данные между нодами;
- если нода падает, данные на ее локальном диске недоступны.

---

## 6. Как раскатывается Nginx Ingress

Где включается:

- `inventory/mycluster/group_vars/k8s_cluster/addons.yml`
  - `ingress_nginx_enabled: true`

Где код:

- `kubespray/roles/kubernetes-apps/ingress_controller/meta/main.yml`
- `kubespray/roles/kubernetes-apps/ingress_controller/ingress_nginx/tasks/main.yml`

Что делает роль ingress-nginx:

1. Создает `namespace ingress-nginx`.
2. Создает RBAC (service account, roles, bindings).
3. Создает ingress class `nginx`.
4. Создает daemonset `ingress-nginx-controller`.
5. Создает service `ingress-nginx`.

В вашей конфигурации service типа `NodePort`:

- `80 -> 30080`
- `443 -> 30443`

Зачем это полезно:

- работает даже без cloud LoadBalancer;
- можно зайти по `https://<node-public-ip>:30443` + Host заголовок.

---

## 7. Как раскатывается Argo CD

Где включается:

- `inventory/mycluster/group_vars/k8s_cluster/addons.yml`
  - `argocd_enabled: true`

Где код роли:

- `kubespray/roles/kubernetes-apps/argocd/tasks/main.yml`

Что происходит в роли:

1. Скачивается `yq`.
2. Формируется список шаблонов ArgoCD.
3. Скачивается upstream `install.yaml` ArgoCD.
4. Манифест копируется на control-plane.
5. Через `yq` принудительно выставляется namespace (обычно `argocd`).
6. Применяется namespace + install манифест.
7. Если задан `argocd_admin_password`, патчится секрет `argocd-secret`.

Начальный логин:

- login: `admin`
- password: из секрета `argocd-initial-admin-secret`

---

## 8. Как Argo CD становится доступным извне

В проекте есть отдельный ingress-манифест:

- `inventory/mycluster/manifests/argocd-ingress.yml`

Что он делает:

- создает Ingress в namespace `argocd`;
- направляет трафик на сервис `argocd-server:443`;
- использует `ingressClassName: nginx`.

В нашем варианте варианте host:

- `argocd.52.20.233.48.nip.io`

И вход через NodePort:

- `https://argocd.52.20.233.48.nip.io:30443`

---

## 9. Где физически лежат все важные файлы

### В репозитории `heritage-kubespray-automatic`

- inventory:
  - `inventory/mycluster/inventory.ini`
  - `inventory/mycluster/group_vars/all/all.yml`
  - `inventory/mycluster/group_vars/k8s_cluster/k8s-cluster.yml`
  - `inventory/mycluster/group_vars/k8s_cluster/addons.yml`
  - `inventory/mycluster/manifests/argocd-ingress.yml`

- scripts:
  - `scripts/bootstrap.sh`
  - `scripts/cluster-up.sh`
  - `scripts/cluster-upgrade.sh`
  - `scripts/ui.sh`

- UI:
  - `ui/app.py`
  - `ui/templates/index.html`
  - `ui/static/app.js`

- Kubespray orchestration:
  - `kubespray/playbooks/cluster.yml`

### На control-plane ноде во время применения

Kubespray рендерит/кладет addon manifests в:

- `/etc/kubernetes/addons/ingress_nginx/*`
- `/etc/kubernetes/addons/local_path_provisioner/*`
- `/etc/kubernetes/addons/local_volume_provisioner/*`
- `/etc/kubernetes/argocd-install.yml` и related manifests

---

## 10. Как это выглядит как «история одного запуска»

Допустим, вы запускаете:

```bash
./scripts/cluster-up.sh --cluster mycluster
```

Происходит:

1. Скрипт проверяет inventory.
2. Запускает ansible-playbook `kubespray/cluster.yml`.
3. Kubespray ставит базу (runtime, etcd, control-plane, kubeadm, CNI).
4. Kubespray ставит аддоны (storage, ingress, argocd).
5. Скрипт синхронизирует kubeconfig локально.
6. Вы можете выполнять `kubectl` сразу с вашей машины.

Если на шаге аддонов API временно нестабилен:

- `cluster-up.sh` делает повторную попытку (retry).

---

## 11. Что делать новичку после первой успешной раскатки

Сразу выполните:

```bash
kubectl get nodes -o wide
kubectl get pods -A
kubectl get storageclass
kubectl -n ingress-nginx get svc ingress-nginx
kubectl -n argocd get pods
```

Потом проверьте Argo CD:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d && echo
```

И зайдите в UI ArgoCD в браузере.

Enjoy!