# Boundary Observation Construction Contract

Status: bounded 0.2.x freshness/target-state prerequisite.

NazeYatta already uses Boundary Observations for Re-KY. This contract makes construction reusable
so callers do not have to hand-build the task/handoff/source bindings.

## Public helper

`build_boundary_observation(...)` takes:

- one exact `FreshHandoff`;
- an observation id;
- an observed target binding;
- observed authority/policy/evidence source bindings;
- observer identity metadata;
- an explicit observation timestamp.

It derives:

- `task_id` from the handoff;
- `handoff_fingerprint` from the exact handoff.

It rejects an observation if:

- target identifier does not match the handoff intended target;
- authority ref does not match the handoff authority source ref;
- policy ref does not match the handoff policy source ref;
- evidence-ref set does not match the handoff evidence refs;
- observation structure is malformed.

```text
Observation Built
!= Source Authenticated
!= Authority Granted
```

## Independent consumption validation remains

The Re-KY gate still validates observations when consuming them. It does not assume an observation
is safe merely because a caller could have used the builder.

```text
Builder Used != Consumer Trust
```

This matters because an observation may arrive from a serialized/external path rather than from the
in-process helper.

## Runtime-state boundary

FreshHandoff continues to declare:

```text
runtime_state_bound = false
```

Creating a Boundary Observation does not silently flip that field or extend handoff validity.

The current mechanism is:

```text
FreshHandoff
-> explicit Boundary Observation
-> explicit before/after Re-KY comparison
```

not:

```text
FreshHandoff
-> permanently fresh
```

## Current scope

The production-independent dogfood uses local fixture observations only.

Still not implemented:

- production source adapters;
- receipt-to-target freshness binding;
- TTL/wall-clock expiry;
- source qualification;
- observer authentication;
- authority authentication.

```text
Observed Local Fixture != Production Observer
Boundary Observation != Receipt Freshness Proof
```
