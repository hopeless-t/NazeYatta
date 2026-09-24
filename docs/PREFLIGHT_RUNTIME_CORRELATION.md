# Preflight / Runtime Correlation Contract

Status: bounded 0.2.x prerequisite for later freshness work.

This contract correlates exact preflight and runtime-side artifacts without claiming that their
semantics are equivalent or that the observed runtime state is still fresh.

## Record

`PreflightRuntimeCorrelationRecord` binds:

- exact preflight Receipt fingerprint;
- exact Task fingerprint;
- exact Policy bundle fingerprint;
- exact FreshHandoff fingerprint;
- exact Boundary Observation fingerprint;
- shared `task_id`;
- observed target binding;
- observation timestamp.

Construction re-runs deterministic preflight evaluation and requires the supplied Receipt to match
exactly.

```text
Supplied Receipt
-> re-evaluate exact Task + Policy
-> exact equality required
```

The Boundary Observation is independently validated against the exact FreshHandoff.

## Outcome

A successful record says only:

```text
correlation_outcome = EXACT_ARTIFACTS_BOUND
semantic_equivalence_verified = false
freshness_verified = false
authority_granted = false
```

The word "correlation" is deliberate.

The current generic preflight Task does not require a runtime target identity. A shared `task_id`
and exact artifact fingerprints therefore do not prove that:

```text
Preflight Task semantics
==
KY declaration semantics
==
FreshHandoff intended action
==
Observed runtime target
```

That stronger relation needs a separate explicit contract.

## Why this exists before freshness

A freshness claim must first establish which exact preflight result and which exact runtime
observation are being compared.

Without this bridge, a freshness sidecar could accidentally associate unrelated artifacts.

```text
Same Project != Same Task
Same task_id != Semantic Equivalence Proven
Artifact Correlation != Freshness
```

## Consumer validation

The public `validate_boundary_observation_for_handoff(...)` helper performs read-only validation of
one serialized Boundary Observation against one exact FreshHandoff.

The Re-KY gate continues validating its own inputs independently.

```text
Builder Used != Consumer Trust
Correlation Record Exists != Freshness Verified
```

## Current dogfood

The safe-read dogfood now also executes:

```text
generic preflight Task
-> Receipt
-> FreshHandoff
-> before Boundary Observation
-> PreflightRuntimeCorrelationRecord
```

and asserts that the exact-artifact correlation succeeds while semantic-equivalence/freshness
claims remain false.

This is still local-fixture dogfood.

```text
Dogfood Correlation != Production Correlation
```

## Explicit non-goals

This tranche does not add:

- Receipt fields;
- TTL / wall-clock expiry;
- target semantics to generic Task;
- semantic-equivalence proof;
- production observers;
- evidence-source qualification;
- authority authentication;
- execution authority.
