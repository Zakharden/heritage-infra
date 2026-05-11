# Contributing

This repository is maintained as a public infrastructure reference. Contributions should keep the repository safe to inspect, clone, and review.

## Contribution Guidelines

- Keep changes small and reviewable.
- Prefer documentation and validation improvements before changing runtime behavior.
- Do not commit secrets, private infrastructure data, kubeconfigs, or real credentials.
- Use placeholders for environment-specific values.
- Document assumptions, prerequisites, and rollback considerations.
- Keep generated or vendored changes separate from handwritten source changes when practical.

## Validation Expectations

Choose checks that match the changed area:

- Markdown documentation: review links and formatting.
- Ansible: run syntax checks or `ansible-lint` when available.
- Helm charts: run `helm lint` and `helm template`.
- Kubernetes manifests: render and validate with a manifest validation tool when available.
- Security-sensitive changes: run a secret scanner before pushing.

If a check cannot be run locally, describe the blocker in the pull request.

## Pull Request Structure

A good pull request should include:

- what changed;
- why it changed;
- whether runtime behavior changes;
- validation performed;
- any follow-up work that is intentionally out of scope.

## Runtime Safety

Avoid mixing documentation-only hardening with runtime changes. Infrastructure changes should be isolated so they can be reviewed, tested, and rolled back independently.
