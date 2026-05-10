# Validation Guide

## Goal

This guide describes recommended checks before applying infrastructure-related changes from this repository.

These checks are advisory and should be adapted to the target environment.

## General Checks

- Review changed files manually.
- Confirm no secrets or private values are present.
- Validate YAML syntax where applicable.
- Confirm placeholders were not replaced with real credentials.
- Check that environment-specific assumptions are documented.
- Identify whether a change is documentation-only or can affect execution.

## Suggested Tools

Depending on the changed files, useful tools may include:

- `yamllint`
- `ansible-lint`
- `helm lint`
- `helm template`
- `kubeconform`
- `kubectl --dry-run=server`
- `gitleaks`
- `trivy config`

These tools are listed as recommended validation options. They should be wired into CI only after the exact command set and expected failure behavior are confirmed.

## Ansible Validation

Recommended checks:

- validate inventory structure;
- review variable precedence;
- avoid hardcoded private environment values;
- document required external dependencies;
- run syntax and lint checks where available;
- test changes in a disposable environment before reuse.

## Helm and Kubernetes Validation

Recommended checks:

- render templates before applying;
- validate generated manifests;
- review RBAC changes carefully;
- confirm namespace assumptions;
- document required secrets and config maps;
- compare rendered output before and after a change.

## GitOps Review

Before syncing changes:

- confirm rendered output is expected;
- review drift implications;
- document rollback assumptions;
- avoid committing environment-specific secrets;
- verify that the target branch and path match the intended environment.

## Secret Scanning

Before merging infrastructure changes, check for:

- cloud access keys;
- kubeconfigs;
- private keys;
- tokens;
- real hostnames or IPs tied to private environments;
- customer or employer-specific values.

## Evidence Notes

For public engineering evidence, useful proof may include:

- validation command output;
- PR review discussion;
- CI result;
- screenshots of rendered manifests where appropriate;
- links to merged changes;
- release notes or changelog entries after merge.
