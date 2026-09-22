# Boundary Observation / Re-KY Gate v0.2

Status:

```text
TYPE = BOUNDARY-ONLY CHANGE / OBSERVATION-QUALITY DETECTOR
SOURCE-SPECIFIC RUNTIME ADAPTERS = NOT IMPLEMENTED
WORKER SPAWN = NOT IMPLEMENTED
AUTOMATIC RE-KY GENERATION = NOT IMPLEMENTED
AUTHORITY GRANT = NEVER
```

## Purpose

A Fresh Worker is allowed only one bounded execution bounce by the current handoff contract.

Before deciding whether another bounce may reuse the previous KY work, compare the execution boundary **and whether critical source bindings were actually observed**.

```text
FreshHandoff
+ Before BoundaryObservation
+ After BoundaryObservation
        |
        v
CONTINUE / RE_KY
```

## Observation states

Source bindings use one of three explicit states:

```text
OBSERVED
CARRIED_FORWARD
UNKNOWN
```

- `OBSERVED`: the observation source supplied a current binding token;
- `CARRIED_FORWARD`: the reference was copied from prior state/handoff without re-observing the source;
- `UNKNOWN`: the current source binding is unavailable.

```text
CARRIED_FORWARD != OBSERVED
UNKNOWN != OBSERVED
Reference Present != Source Observed
```

For generic sources the change value is called a `binding_token`, not a fingerprint. A future source adapter may use a digest, revision, etag, version, or another stable token.

```text
Binding Token != Source Authenticated
Observed Token != Authority Proven
```

## Fail-closed CONTINUE rule

`CONTINUE` requires all critical authority, policy, and evidence bindings to be `OBSERVED` in both snapshots and unchanged.

If a critical source is `CARRIED_FORWARD` or `UNKNOWN`, the result is `RE_KY`.

```text
Unobserved Critical Source -> RE_KY
CONTINUE != Execution Authority
Boundary Unchanged != World Unchanged
```

## Evidence binding rule

An evidence binding contains:

- source ref;
- observation state;
- evidence state;
- binding token.

When evidence is not `OBSERVED`:

```text
binding_token = null
state = UNKNOWN
```

This prevents copied or unavailable evidence from being represented as VERIFIED.

Observed evidence may still trigger `RE_KY` if:

- its binding token changes;
- its evidence state changes;
- it becomes STALE / INVALID / MISSING / UNKNOWN.

## Target boundary

Target identity remains directly represented by:

```text
kind
identifier
identity_fingerprint
```

The comparator deliberately does not hash the entire mutable target content.

```text
Target Content Changed != Execution Boundary Changed
```

## Cross-stage binding

The comparator receives the actual FreshHandoff object and recomputes its fingerprint.

The before observation must bind to:

- handoff task ID;
- actual handoff fingerprint;
- intended target;
- authority ref;
- policy ref;
- evidence-ref set.

Only then are before/after snapshots compared.

```text
Two Matching Fake Observations != Valid Continuation
Before Snapshot != Handoff -> Reject
```

## Runtime status

The safe-read dogfood now exercises this gate truthfully:

```text
target identity = observed
authority       = carried forward
policy          = carried forward
evidence        = carried forward / unknown
        |
        v
RE_KY
```

That is a successful fail-closed runtime result, not a positive continuation result.

Source-specific adapters are still future work.
