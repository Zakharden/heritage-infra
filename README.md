# heritage-infra - infrastructure for HSE start-up:


## *ansible_host_settings*
 - набор ansible-playbooks для настройки виртуальных машин. Подготовка вм к раскатке k8s. 

### Функционал

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

---


