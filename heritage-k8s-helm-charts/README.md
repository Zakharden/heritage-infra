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
- `30` - PostgreSQL и Redis

## Что сделать вручную (обязательно)

После того как приложения `heritage-vault`, `heritage-vault-secrets-operator`, `heritage-vault-sync`
перейдут в `Synced/Healthy`, необходимо добавить секреты в Vault вручную:

```bash
# порт-форвард до Vault
kubectl -n vault port-forward svc/heritage-vault 8200:8200

export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=<your-vault-root-token>

# PostgreSQL секреты
vault kv put kv/heritage/postgres \
  postgres-password='<postgres-admin-password>' \
  password='<postgres-app-user-password>' \
  replication-password='<postgres-replication-password>'

# Redis секрет
vault kv put kv/heritage/redis \
  redis-password='<redis-password>'
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
