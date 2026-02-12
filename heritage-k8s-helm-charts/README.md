# heritage-k8s-helm-charts

Helm chart-репозиторий для разворачивания stateful-сервисов в Kubernetes через Argo CD.

## Что внутри

- `postgres/` - wrapper chart над `bitnami/postgresql`
- `redis/` - wrapper chart над `bitnami/redis`
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

### Redis

- режим: standalone (1 инстанс)
- storage: PVC 2Gi
- storageClass: `local-path`
- auth: включен

## Как использовать в Argo CD

1. Запушbnm этот репозиторий в Git.
2. Применить манифесты:

```bash
kubectl apply -f argocd-applications/postgres-application.yaml
kubectl apply -f argocd-applications/redis-application.yaml
```

## Локальная проверка (опционально)

Если на машине установлен `helm`:

```bash
helm dependency update postgres
helm dependency update redis
helm template heritage-postgres ./postgres
helm template heritage-redis ./redis
```
