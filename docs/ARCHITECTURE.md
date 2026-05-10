# Architecture Overview

## Repository Role

`heritage-infra` is a public infrastructure reference project focused on Kubernetes operations, GitOps delivery, and reproducible automation patterns.

It is intended to show how infrastructure responsibilities can be organized and reviewed. It is not a universal production environment.

## Main Areas

- Cluster preparation and inventory assumptions.
- Ansible-based host automation.
- Kubespray-oriented Kubernetes provisioning.
- Helm-based packaging and deployment structure.
- Argo CD / GitOps delivery concepts.
- Vault-oriented secrets management assumptions.
- Operational validation and review notes.

## Repository Map

- `ansible_host_settings` prepares hosts for Kubernetes-related workflows.
- `heritage-kubespray-automatic` organizes Kubespray-based cluster automation and operational scripts.
- `heritage-k8s-helm-charts` contains Helm charts and Argo CD Application manifests for platform services.

## Workflow

1. Prepare infrastructure assumptions.
2. Review inventory and configuration.
3. Run validation before applying changes.
4. Apply automation in a controlled environment.
5. Deliver application or platform changes through a GitOps-style review path.
6. Document operational assumptions and follow-up risks.

## Boundaries

This repository does not include:

- real credentials;
- private environment data;
- guaranteed production configuration;
- cloud-provider-specific production hardening;
- organization-specific access policies;
- a universal backup, restore, or disaster-recovery design.

## Design Principles

- Reviewable infrastructure changes.
- Explicit configuration over hidden manual steps.
- Secret-free public examples.
- Clear operational assumptions.
- Validation before execution.
- Small changes that can be reviewed independently.

## Review Questions

Before reusing or extending this repository, review:

- Which values are environment-specific?
- Which secrets must be provided externally?
- Which commands are safe to run in a disposable environment first?
- Which network, storage, and access assumptions need local adaptation?
- Which rollback path exists if a change fails?
