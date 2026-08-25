# Evidence Model

An artifact alone is not evidence. Evidence should connect an observation to a claim with provenance.

A useful evidence record should bind the claim, the observation, its provenance, and relevant time/state context.

Suggested record:

```yaml
evidence_id: EV-102
supports_claim: target_branch_is_expected
kind: external_observation
artifact:
  remote_sha: b2ef43f...
observed_at: 2026-08-25T16:40:00+09:00
observer:
  type: github_api
verification:
  state: VERIFIED
```

## Freshness / TOCTOU

A preflight receipt must be bound to relevant state. If the task, policy bundle, target state, worker qualification, or evidence changes, the old preflight may be stale.

`Verified At Time T != Currently Verified`.
