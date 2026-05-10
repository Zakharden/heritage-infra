# Contributing

## Project Intent

This repository documents and organizes infrastructure patterns around Kubernetes, Ansible, Kubespray, Helm, GitOps, and secrets-aware automation.

Contributions should improve clarity, safety, reproducibility, or reviewability.

## Contribution Types

Useful contributions include:

- documentation improvements;
- validation steps;
- safer defaults in examples;
- architecture notes;
- linting or review guidance;
- small fixes that make workflows easier to understand;
- examples that use placeholders instead of environment-specific values.

## Before Opening a PR

Please check:

- the change does not include secrets or private infrastructure details;
- examples use placeholders instead of real environment values;
- assumptions are documented;
- commands are safe to review before execution;
- the PR scope is narrow and easy to review;
- any runtime or infrastructure impact is explicitly described.

## Pull Request Checklist

A good PR should explain:

- what changed;
- why it changed;
- which files or components are affected;
- how the change was validated;
- any assumptions or limitations;
- whether the change is documentation-only or may affect execution.

## Style Guidelines

- Prefer English for new governance and architecture documentation.
- Keep operational claims factual and verifiable.
- Avoid unsupported terms such as `production-ready`, `enterprise-grade`, or `battle-tested`.
- Use clear examples instead of broad claims.
- Keep commands copyable and annotate destructive commands clearly.

## Branch Names

Use descriptive branch names without tool/vendor prefixes, for example:

- `docs/validation-guide`
- `docs/security-policy`
- `infra/ansible-host-prep-notes`
- `helm/chart-validation-notes`

## Review Principles

Changes should improve at least one of:

- clarity;
- safety;
- reproducibility;
- maintainability;
- reviewability.
