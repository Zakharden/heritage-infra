# heritage-k8s-helm-charts

Helm chart-репозиторий для разворачивания stateful-сервисов в Kubernetes через Argo CD.

## Что внутри

- `postgres/` - wrapper chart над `bitnami/postgresql`
- `redis/` - wrapper chart над `bitnami/redis`
- `vault/` - wrapper chart над `hashicorp/vault`
- `vault-secrets-operator/` - wrapper chart над `hashicorp/vault-secrets-operator`
- `vault-sync/` - манифесты для bootstrap Vault и синхронизации секретов в K8s
- `argocd-applications/` - готовые манифесты `Application` для Argo CD

## Конфигурация из коробки

### PostgreSQL

- режим: `primary + 1 read replica` (2 инстанса)
- ресурсы:
  - `primary`: 2Gi RAM
  - `replica`: 2Gi RAM
- storage:
  - `primary`: PVC 2Gi
  - `replica`: PVC 2Gi
- storageClass: `local-path` (можно переопределить)
- пароли берутся из `existingSecret`, который синхронизируется из Vault

### Redis

- режим: standalone (1 инстанс)
- storage: PVC 2Gi
- storageClass: `local-path`
- auth: включен
- пароль берется из `existingSecret`, который синхронизируется из Vault


## Helm зависимости (важно для Argo CD)

Wrapper-чарты `postgres/` и `redis/` зависят от Bitnami charts. Чтобы Argo CD не пытался
качать `index.yaml` Helm-репозитория изнутри кластера,
зависимости **вендорятся** в репозиторий:

- `postgres/_vendor/postgresql` (postgresql chart `16.7.27`)
- `redis/_vendor/redis` (redis chart `20.13.4`)

### Vault

- деплой `hashicorp/vault` в namespace `vault`
- режим: `dev` (lab/demo)
- root token задается в:
  - `vault/values.yaml`
  - `vault-sync/secret-vault-root-token.yaml`

### Vault Secrets Operator

- деплой `hashicorp/vault-secrets-operator`
- создает K8s Secrets из Vault:
  - `heritage-postgres-auth`
  - `heritage-redis-auth`

## Где физически хранятся пароли

В Vault (KV-v2):

- `kv/heritage/postgres`
- `kv/heritage/redis`

Bootstrap-логика Vault находится в файле:

- `vault-sync/configmap-vault-bootstrap-script.yaml`

Bootstrap job теперь не записывает пароли в Vault.
Он создает только auth/policy/role для Vault Secrets Operator.

## Как использовать в Argo CD

1. Запушьте этот репозиторий в Git.
2. В `argocd-applications/*.yaml` замените `repoURL` на ваш URL репозитория.
3. Создайте root `Application` (app-of-apps) с path:
   - `heritage-k8s-helm-charts/argocd-applications`
4. Сделайте `Sync` в Argo CD.

Порядок раскатки управляется через `sync-wave`:

- `0` - Vault
- `10` - Vault Secrets Operator
- `20` - Vault bootstrap/sync
- `25` - внешний доступ (Vault Ingress + TCP для Postgres/Redis)
- `30` - PostgreSQL и Redis

## Внешний доступ (Ingress / TCP)

### Vault (HTTP Ingress)

В `external-access/vault-ingress.yaml` создается Ingress для Vault UI/API:

- host: `vault.52.20.233.48.nip.io` (можно поменять под ваш домен)

### PostgreSQL + Redis (TCP через ingress-nginx)

Kubernetes Ingress ресурс предназначен для HTTP/HTTPS. Для PostgreSQL и Redis используется
возможность `ingress-nginx` проксировать TCP через ConfigMap `tcp-services`.

Манифест `external-access/ingress-nginx-tcp-services.yaml` делает:

- `ingress-nginx/tcp-services`:
  - `5432` -> `data/heritage-postgres-postgresql-primary:5432`
  - `6379` -> `data/heritage-redis-master:6379`
- `Service ingress-nginx/ingress-nginx-tcp` (NodePort):
  - Postgres: `31432`
  - Redis: `31379`

Подключение с другого сервера:

```bash
# Postgres
psql -h <k8s_node_public_ip> -p 31432 -U app_user -d app_db

# Redis
redis-cli -h <k8s_node_public_ip> -p 31379 -a '<redis-password>'
```

## Что сделать вручную (обязательно)

После того как приложения `heritage-vault`, `heritage-vault-secrets-operator`, `heritage-vault-sync`
перейдут в `Synced/Healthy`, необходимо добавить секреты в Vault вручную:

```bash
# Вариант A (без установки vault-cli): выполнить команды внутри pod Vault
# Root token по умолчанию (dev): `pass_heritage`
kubectl -n vault exec -it heritage-vault-0 -- sh

export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=pass_heritage

# PostgreSQL секреты
vault kv put kv/heritage/postgres \
  postgres-password='<postgres-admin-password>' \
  password='<postgres-app-user-password>' \
  replication-password='<postgres-replication-password>'

# Redis секрет
vault kv put kv/heritage/redis \
  redis-password='<redis-password>'

exit

# Вариант B: порт-форвард + vault-cli (если установлен на вашей машине)
# kubectl -n vault port-forward svc/heritage-vault 8200:8200
# export VAULT_ADDR=http://127.0.0.1:8200
# export VAULT_TOKEN=pass_heritage
# vault kv put ...
```

После этого Vault Secrets Operator создаст/обновит K8s secrets:

- `heritage-postgres-auth` (namespace `data`)
- `heritage-redis-auth` (namespace `data`)

И только затем PostgreSQL/Redis смогут корректно стартовать.

## Локальная проверка (опционально)

Если на машине установлен `helm`:

```bash
helm dependency update vault
helm dependency update vault-secrets-operator
helm dependency update postgres
helm dependency update redis

helm template heritage-vault ./vault
helm template heritage-vault-secrets-operator ./vault-secrets-operator
helm template heritage-postgres ./postgres
helm template heritage-redis ./redis
```
