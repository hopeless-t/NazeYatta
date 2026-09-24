# Release authority route

This repository uses two separate external publication boundaries:

1. GitHub technical prerelease publication.
2. PyPI package publication.

Both write boundaries are protected by the GitHub Actions Environment named `release`.

## Operator sequence

1. Prepare and review an exact release candidate on `main`.
2. Dispatch `Publish GitHub Technical Prerelease` from `main` with the version and exact final commit.
3. Inspect the build/verification result and hashes.
4. Approve the `release` Environment deployment only when GitHub publication is intended.
5. Confirm GitHub Release readback succeeds.
6. Dispatch `Publish NazeYatta to PyPI` from `main` with the same version and final commit.
7. Approve the second `release` Environment deployment only when PyPI publication is intended.
8. Confirm PyPI metadata and re-downloaded artifacts match the GitHub Release hashes.

The two approvals are intentional. GitHub Release and PyPI are different irreversible external writes even though they share one Environment policy.

## Authority and evidence boundaries

```text
Workflow Dispatch != Publication Authorization
Environment Waiting != Approval
Environment Approval != Universal Authority Authentication
GitHub Release Published != PyPI Published
PyPI OIDC Accepted != Package Uploaded
Build PASS != Runtime/Production Readiness
Exact Artifact Correlation != Freshness
```

The workflows record a live target observation immediately before each external-write step and perform post-write readback. A future real publication can therefore provide evidence for the observation-to-write relation tracked in Issue #54. Merely having this instrumentation in source does not establish freshness.

## Safety properties

- Publication workflows are `workflow_dispatch` only.
- There is no `push` or scheduled publication trigger.
- GitHub `contents: write` exists only on the Human-gated GitHub publication job.
- PyPI `id-token: write` exists only on the Human-gated PyPI publication job.
- Both workflows share the `nazeyatta-release` concurrency group.
- The PyPI workflow filename remains `publish-pypi-0.2.0a1.yml` because that filename is part of the configured Trusted Publisher identity.

Release workflow configured != release authorized.