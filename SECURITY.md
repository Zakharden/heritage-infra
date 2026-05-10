# Security Policy

## Scope

This repository is a public infrastructure reference project. It may contain examples for Kubernetes, Ansible, Helm, GitOps, and secrets-oriented workflows, but it must not contain real credentials, private keys, kubeconfigs, tokens, customer data, or employer-owned infrastructure details.

## Supported Use

The repository is intended for review, learning, and reference implementation purposes. It is not an SLA-backed product or a drop-in production environment.

## Reporting a Security Issue

If you find a security issue, please do not publish exploit details in a public issue first.

Preferred reporting path:

- open a private GitHub security advisory if available; or
- contact the repository maintainer directly through GitHub contact options.

Please include:

- affected file or component;
- clear reproduction steps;
- expected risk;
- suggested remediation if known.

## Secret Handling

Do not commit:

- tokens, credentials, kubeconfigs, cloud keys, or private keys;
- real inventory data;
- private IP ranges tied to non-public environments;
- employer, customer, or internal infrastructure details.

Use placeholders for examples and document where environment-specific values must be supplied by the operator.

## Security Review Checklist

Before opening a PR, check:

- no secrets are included;
- examples use placeholders;
- access assumptions are documented;
- RBAC and security-sensitive changes are explained;
- validation steps are included where practical;
- generated files do not expose private environment details.
