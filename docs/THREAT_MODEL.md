# Threat Model

This document records the main security assumptions for `heritage-infra`. It is intentionally practical: the repository is public, so the safest default is to assume every committed value can be read and reused by anyone.

## Scope

In scope:

- public repository contents;
- Ansible host preparation;
- Kubespray inventory and cluster variables;
- Argo CD Application manifests;
- Helm values and platform service configuration;
- Vault bootstrap and Vault Secrets Operator manifests;
- documentation and examples.

Out of scope:

- private production infrastructure;
- cloud account identity and IAM policies not stored in this repository;
- runtime secrets stored outside Git;
- incident response systems outside the repository.

## Assets

| Asset | Why it matters |
|---|---|
| Kubernetes admin access | Full control over workloads, secrets, and cluster state. |
| SSH access to nodes | Direct host-level access to infrastructure. |
| Vault root/admin credentials | Ability to read or write all managed secrets. |
| Database credentials | Access to application data. |
| Git history | Public record of infrastructure assumptions and possible historical mistakes. |
| Argo CD repository access | Control over deployed desired state. |

## Trust Boundaries

- GitHub repository boundary: everything committed here is public information.
- Operator workstation boundary: kubeconfig, SSH keys, cloud credentials, and Vault tokens must stay local or in an approved secret manager.
- Kubernetes cluster boundary: service accounts and Kubernetes secrets must be scoped to the namespace and workload that need them.
- Vault boundary: Vault is the intended source of application secrets, not Git.

## Key Risks And Controls

| Risk | Control |
|---|---|
| Committing real secrets or kubeconfigs | Keep secrets out of Git, use placeholders, and scan commits with a secret scanner before pushing. |
| Reusing lab endpoints in a real environment | Treat inventory and public host examples as environment-specific; replace before deployment. |
| Exposing stateful services broadly | Restrict ingress, node ports, security groups, and firewall rules to known source networks. |
| Using Vault dev mode outside a lab | Replace dev mode with a production Vault deployment model, persistent storage, unseal strategy, and audited access. |
| Over-privileged service accounts | Review RBAC for Argo CD, Vault Secrets Operator, and bootstrap jobs before production use. |
| Unreviewed cluster upgrades | Use a separate upgrade branch, maintenance window, and rollback plan. |
| Lost data from local storage assumptions | Define backup, restore, and persistent volume migration procedures before storing important data. |

## Pre-Deployment Checklist

- [ ] Replace public/lab inventory values with environment-specific hosts.
- [ ] Confirm no private keys, kubeconfigs, cloud credentials, tokens, or real passwords are committed.
- [ ] Run a secret scan against the branch.
- [ ] Render Helm templates before applying them.
- [ ] Review Kubernetes RBAC and service account permissions.
- [ ] Limit external ingress and TCP exposure to approved networks.
- [ ] Define backup and restore procedures for PostgreSQL, Redis, and Vault data.
- [ ] Document manual prerequisites and rollback steps.

## Evidence Notes

For public portfolio and review purposes, this threat model demonstrates the security reasoning behind the repository. It does not certify that a running deployment is production-ready; production readiness depends on the target environment and operational controls.
