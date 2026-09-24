# Release authority route

This repository uses two separate external publication boundaries:

1. GitHub release publication (`stable` or `prerelease` channel).
2. PyPI package publication.

Both write boundaries are protected by the GitHub Actions Environment named `release`.

## Operator sequence

1. Prepare and review an exact release candidate on `main`.
2. Dispatch `Publish GitHub Release` from `main` with the version, exact final commit, and intended `stable` / `prerelease` channel.
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

The workflows record a live target observation immediately before each external-write step and perform post-write readback. The v0.2.0a4 GitHub/PyPI publication exercised this path and supplied the bounded real-write evidence that completed Issue #54. That concrete result does not imply universal freshness for unrelated consumers.

## Safety properties

- Publication workflows are `workflow_dispatch` only.
- There is no `push` or scheduled publication trigger.
- GitHub `contents: write` exists only on the Human-gated GitHub publication job.
- PyPI `id-token: write` exists only on the Human-gated PyPI publication job.
- Both workflows share the `nazeyatta-release` concurrency group.
- The PyPI workflow filename remains `publish-pypi-0.2.0a1.yml` because that filename is part of the configured Trusted Publisher identity.

Release workflow configured != release authorized.

Stable release channel != production enforcement claim.