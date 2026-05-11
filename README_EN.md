# heritage-infra

## Executive Overview

`heritage-infra` is a public infrastructure reference project focused on Kubernetes operations, GitOps delivery, and reproducible automation patterns.

The repository demonstrates how infrastructure components can be organized, documented, and reviewed across a platform engineering workflow: host preparation, cluster provisioning, application delivery, secrets-oriented design, and operational validation.

This project should be read as an engineering lab and reference implementation, not as a drop-in production environment.

## Project Scope

The repository focuses on:

- Kubernetes infrastructure preparation and operational structure.
- Ansible-based automation and configuration workflows.
- Kubespray-oriented cluster provisioning patterns.
- Helm-based application packaging and deployment structure.
- Argo CD / GitOps-style delivery concepts.
- Vault-oriented secrets management assumptions.
- Clear documentation of infrastructure responsibilities, boundaries, and validation steps.

## Repository Areas

- `ansible_host_settings` - base host preparation for Kubernetes nodes.
- `heritage-kubespray-automatic` - Kubespray-based cluster automation and operational scripts.
- `heritage-k8s-helm-charts` - Helm charts and Argo CD Application manifests for platform services.

## Architecture and Workflow

The intended workflow is:

1. Prepare infrastructure and inventory assumptions.
2. Use automation to configure the target environment.
3. Provision or manage Kubernetes components through repeatable configuration.
4. Package platform/application components with Helm where appropriate.
5. Deliver changes through a GitOps-oriented review and deployment flow.
6. Keep operational assumptions explicit so other engineers can review the setup safely.

Key engineering principles used in this repository:

- infrastructure changes should be reviewable before execution;
- configuration should be explicit rather than hidden in manual steps;
- secrets should not be committed to the repository;
- platform components should have documented ownership and purpose;
- validation should be performed before applying changes to any real environment.

For the full architecture map, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Safety Notes

This repository must not contain:

- real credentials, tokens, kubeconfigs, private keys, or cloud secrets;
- customer, employer, or private infrastructure data;
- undocumented production assumptions;
- environment-specific values that cannot be safely shared publicly.

Before reusing any part of this repository, review and adapt:

- inventory files;
- network assumptions;
- storage configuration;
- access control and RBAC;
- secret management;
- cloud or VM-specific settings;
- backup and rollback procedures.

## Validation Notes

Recommended validation before applying infrastructure changes:

- review YAML, inventory, and Helm values for syntax and environment-specific assumptions;
- run relevant linters where available, such as `yamllint`, `ansible-lint`, `helm lint`, and Kubernetes manifest validation tools;
- perform dry-run or template rendering checks before deployment;
- verify that no secrets or private environment details are present in commits;
- document any manual prerequisites clearly before running automation;
- test changes in a disposable or non-production environment first.

For security assumptions, threat boundaries, and pre-deployment controls, see:

- [SECURITY.md](SECURITY.md)
- [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)

## Related Documentation

The main README remains in Russian and contains the detailed current walkthrough:

- [README.md](README.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md)
- [SECURITY.md](SECURITY.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)
- `ansible_host_settings/README.md`
- `heritage-kubespray-automatic/README.md`
- `heritage-kubespray-automatic/docs/OPERATIONS_GUIDE_RU.md`
- `heritage-kubespray-automatic/docs/LEARNING_CLUSTER_FROM_ZERO_RU.md`
- `heritage-k8s-helm-charts/README.md`
