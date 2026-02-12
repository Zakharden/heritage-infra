Базовая настройка VM на RHEL 9 под Kubernetes.

## Функционал

1. На **всех** узлах:
   - установка базовых пакетов;
   - создание пользователя `viewer` без root/sudo прав;
   - настройка времени (`chronyd`, timezone);
   - отключение swap (текущее + `/etc/fstab`);
   - sysctl и модули ядра для Kubernetes;
   - установка и настройка `containerd` (`SystemdCgroup=true`);
   - установка `kubelet`, `kubeadm`, `kubectl`, `cri-tools`;
   - создание рабочих директорий (`/var/lib/kubelet`, `/var/lib/containerd`, `/var/log/kubernetes`, `/opt/k8s/bin`, `/data`);
   - ограничение размера systemd-journald под диск 40 GB;
   - авторасширение корневого раздела (если автоматически определяется схема диска);
   - открытие базовых портов Kubernetes в firewalld.

2. Только на **master**:
   - установка `python3.11` и `python3.11-pip`;
   - проверка установленной версии Python 3.11.

## Топология (inventory)

- `vm-k8s-m1` (`52.20.233.48`, `172.31.70.213`) - `master + infra`
- `vm-k8s-w1` (`34.194.182.115`, `172.31.17.45`) - `worker`
- `vm-k8s-w2` (`23.23.33.244`, `172.31.59.144`) - `worker`

Файл: `inventory/hosts.ini`


## Теги в playbook

Основные теги:
- `baseline` - базовая настройка хоста
- `packages` - установка/обновление пакетов
- `user` - создание и настройка пользователя `viewer`
- `time` - timezone и `chronyd`
- `k8s` - подготовка узла под Kubernetes
- `system` - системные настройки ОС
- `containers` - runtime и containerd
- `network` - сетевые параметры и firewall
- `storage` - директории, journald, disk grow
- `security` - настройки безопасности
- `checks` - проверки и assert-задачи
- `master` - задачи только для master-узла
- `infra` - задачи infra-роли master-узла
- `python311` - установка Python 3.11 на master

## Какие теги в каком playbook

| Playbook | Play / Role | Hosts | Tags |
|---|---|---|---|
| `playbooks/site.yml` | `Подготовка всех узлов RHEL 9 под Kubernetes` / `common` | `k8s_cluster` | `baseline`, `packages`, `user`, `time`, `checks`, `security` |
| `playbooks/site.yml` | `Подготовка всех узлов RHEL 9 под Kubernetes` / `k8s_prereqs` | `k8s_cluster` | `k8s`, `system`, `containers`, `network`, `storage`, `swap`, `packages`, `checks`, `security` |
| `playbooks/site.yml` | `Дополнительная настройка master + infra` / `master_extra` | `master` | `master`, `infra`, `python311`, `packages`, `checks` |

## Подготовка окружения

Из директории `/home/ec2-user/ansible_host_settings`:

```bash
chmod +x scripts/bootstrap_env.sh
./scripts/bootstrap_env.sh
```

После этого можно:

```bash
source .venv/bin/activate
```

или запускать Ansible без активации:

```bash
./.venv/bin/ansible-playbook -i inventory/hosts.ini playbooks/site.yml
```

## Запуск

Из директории `/home/ec2-user/ansible_host_settings`:

```bash
./.venv/bin/ansible -i inventory/hosts.ini all -m ping
./.venv/bin/ansible-playbook -i inventory/hosts.ini playbooks/site.yml
```

Примеры запуска по тегам:

```bash
# Только создание viewer + nano + база
./.venv/bin/ansible-playbook -i inventory/hosts.ini playbooks/site.yml --tags "baseline,user,packages"

# Только k8s-подготовка
./.venv/bin/ansible-playbook -i inventory/hosts.ini playbooks/site.yml --tags "k8s"

# Только python3.11 на master
./.venv/bin/ansible-playbook -i inventory/hosts.ini playbooks/site.yml --tags "master,python311"
```

Если у вас установлен `make`, можно использовать сокращения из `Makefile` (`venv`, `ping`, `run`, `baseline`, `k8s`, `master-python`).

## Важные переменные

Файл `inventory/group_vars/all.yml`:
- `k8s_repo_version`: ветка репозитория Kubernetes (по умолчанию `v1.30`);
- `viewer_ssh_public_keys`: SSH-ключи для пользователя `viewer` (пусто по умолчанию);
- `k8s_set_selinux_permissive`: перевод SELinux в permissive (`true` по умолчанию);
- `enable_rootfs_autogrow`: авторасширение root FS (`true` по умолчанию);
- `enable_firewalld_for_k8s`: настройка firewalld (`true` по умолчанию).