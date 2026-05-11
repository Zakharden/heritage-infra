# Security Policy

## Public Repository Assumptions

This repository is public and should be treated as a reference implementation, lab environment, and documentation baseline. Do not commit production secrets or private infrastructure data.

Never commit:

- private SSH keys;
- kubeconfig files with live credentials;
- Vault tokens or unseal keys;
- cloud access keys;
- database passwords;
- customer or employer data;
- private network diagrams that cannot be shared publicly.

## Secret Handling

Application credentials should be stored in Vault or another approved secret manager, then synchronized to Kubernetes through controlled mechanisms such as Vault Secrets Operator.

Git should contain only:

- templates;
- placeholders;
- documented paths;
- non-sensitive example values;
- instructions for creating real values outside the repository.

## Reporting Security Issues

If you find a security issue in this repository, please open a GitHub issue only if the report does not contain sensitive details.

For sensitive findings, contact the repository owner privately through the contact methods listed on the GitHub profile.

## Before Reusing This Repository

Before adapting any part of this repository to a real environment:

- rotate any lab credentials;
- replace public endpoints and inventory examples;
- review firewall and security group exposure;
- validate Vault deployment mode;
- review Kubernetes RBAC and service accounts;
- run a secret scanner against your branch;
- test changes in a disposable environment.

## Supported Scope

This repository does not provide production support guarantees. It is maintained as a public engineering reference and should be reviewed before use in any environment with real users or data.
