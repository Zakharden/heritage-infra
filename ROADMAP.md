# Roadmap

This roadmap describes planned improvements for `heritage-infra` as a public infrastructure reference project.

It is not a delivery commitment.

## Near-Term

- Improve English documentation for repository structure and workflows.
- Add validation guidance for Ansible, Helm, Kubernetes manifests, and GitOps review.
- Document secret handling expectations.
- Add contribution and security guidelines.
- Clarify GitOps workflow assumptions.

## Medium-Term

- Add examples for rendered Helm output validation.
- Add CI checks for documentation, YAML, and infrastructure configuration where practical.
- Add architecture diagrams or workflow diagrams.
- Improve examples around environment separation.
- Document rollback and recovery considerations.

## Long-Term

- Build a clearer reference path from infrastructure preparation to GitOps delivery.
- Add repeatable local validation examples.
- Track meaningful open-source and documentation improvements through changelog entries.
- Keep the repository safe for public review without exposing private infrastructure details.

## Non-Goals

- Publishing private infrastructure configuration.
- Claiming production readiness without public validation.
- Supporting every Kubernetes distribution or cloud provider.
- Replacing environment-specific security review.
- Storing credentials, kubeconfigs, private keys, or organization-specific access policies.
