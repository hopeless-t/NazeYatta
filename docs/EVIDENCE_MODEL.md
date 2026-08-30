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
  observed_at: "2026-08-25T16:40:00+09:00"
observer:
  type: github_api
verification:
      state: VERIFIED
```

## v0.2 task-reference lane

`schema_version: "0.2"` tasks reference records rather than placing an evidence state directly under a policy claim:

```yaml
evidence:
  target_identity_verified: EV-TARGET-001
evidence_records:
  EV-TARGET-001:
    evidence_id: EV-TARGET-001
    supports_claim: target_identity_verified
    observed_at: "2026-08-25T16:40:00+09:00"
    observer: {type: human_or_adapter}
    verification: {state: VERIFIED}
```

For a policy-required claim the evaluator requires the referenced record to exist, have the matching `evidence_id`, support that same claim, contain an observation time and observer type, and use one of the canonical uppercase states. It then uses that state as the effective state. Missing references are `MISSING`; malformed or mismatched records are `INVALID`.

This checks input linkage, not real-world identity or authority:

```text
Document Author != Field Authority
Producer Identity != Evidence Authority
Worker Self-Declaration != Evidence
Provenance Present != Authority Proven
Evidence VERIFIED != Execution Authority
```

The unversioned/v0.1 scalar form remains a compatibility lane only. A scalar `VERIFIED` is not retroactively provenance-qualified, and a `PASS` never grants execution authority.

## Freshness / TOCTOU

A preflight receipt must be bound to relevant state. If the task, policy bundle, target state, worker qualification, or evidence changes, the old preflight may be stale.

`Verified At Time T != Currently Verified`.
