# Policy Model

A NazeYatta policy bundle is an input with its own provenance and authority. A rule merely existing in a repository does not make it normative.

Recommended metadata for production use:

```yaml
policy_id: MVCA-PUB-001
version: 3
status: ACTIVE
owner:
  authority: project_policy_owner
scope:
  operations: [publish]
source:
  repository: example/repo
  revision: abc123
```

## Applicability

Applicability should support at least:

- `APPLIES`
- `DOES_NOT_APPLY`
- `UNKNOWN`

`Failed Matching != DOES_NOT_APPLY`.

## Effects

Typed effects are preferred over one universal safety boolean:

- `NO_EFFECT`
- `WARN`
- `CAUTION`
- `REVIEW`
- `EVIDENCE_REQUIRED`
- `BLOCK`
- `ESCALATE`

v0.1 implements a small subset in the evaluator.
