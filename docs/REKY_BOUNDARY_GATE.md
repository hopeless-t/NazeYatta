# Boundary Observation / Re-KY Gate v0.2

Status:

```text
TYPE = BOUNDARY-ONLY CHANGE / OBSERVATION-QUALITY DETECTOR
DOGFOOD FIXTURE SOURCE OBSERVER = IMPLEMENTED IN STACKED DOGFOOD TRANCHE
GENERAL SOURCE ADAPTERS = NOT IMPLEMENTED
AUTOMATIC RE-KY GENERATION = NOT IMPLEMENTED
AUTHORITY GRANT = NEVER
```

## Purpose

Before another execution bounce reuses the previous KY work, compare the execution boundary and the quality of its source observations.

```text
FreshHandoff
+ Before BoundaryObservation
+ After BoundaryObservation
        |
        v
CONTINUE / RE_KY
```

## Observation states

Critical source bindings use:

```text
OBSERVED
CARRIED_FORWARD
UNKNOWN
```

- `OBSERVED`: the observation source supplied a current binding token.
- `CARRIED_FORWARD`: the reference came from prior state but was not re-observed.
- `UNKNOWN`: no current binding is available.

```text
CARRIED_FORWARD != OBSERVED
UNKNOWN != OBSERVED
Reference Present != Source Observed
```

Generic source change values are called `binding_token`.

A binding token may be a digest, revision, etag, version, or another adapter-defined stable change token.

```text
Binding Token != Source Authenticated
Observed Token != Authority Proven
```

## Fail-closed CONTINUE rule

A positive `CONTINUE` requires:

- authority binding OBSERVED before and after;
- policy binding OBSERVED before and after;
- every evidence binding OBSERVED before and after;
- source refs unchanged;
- binding tokens unchanged;
- evidence states acceptable and unchanged;
- target identity unchanged;
- observation source unchanged.

If a critical source is `CARRIED_FORWARD` or `UNKNOWN`:

```text
RE_KY
```

```text
CONTINUE != Execution Authority
Boundary Unchanged != World Unchanged
```

## Evidence rule

When evidence is not OBSERVED:

```text
binding_token = null
state = UNKNOWN
```

This prevents copied evidence from being represented as VERIFIED.

Observed evidence can still trigger Re-KY when:

- binding token changes;
- evidence state changes;
- state degrades to STALE / INVALID / MISSING / UNKNOWN.

## Target boundary

Target identity is represented independently from mutable target contents:

```text
kind
identifier
identity_fingerprint
```

```text
Target Content Changed != Execution Boundary Changed
```

## Cross-stage binding

The comparator receives the actual FreshHandoff and recomputes its fingerprint.

The before observation must bind to:

- task ID;
- actual handoff fingerprint;
- intended target;
- authority ref;
- policy ref;
- evidence-ref set.

```text
Two Matching Fake Observations != Valid Continuation
Before Snapshot != Handoff -> Reject
```

## Runtime dogfood progression

Two runtime cases are intentionally distinguished.

### Unobserved-source case

When source refs are merely carried forward:

```text
target     = OBSERVED
authority  = CARRIED_FORWARD
policy     = CARRIED_FORWARD
evidence   = CARRIED_FORWARD / UNKNOWN
        |
        v
RE_KY
```

### Fixed-fixture observed case

A stacked dogfood-only fixture observer reads the actual configured local source files before and after execution:

```text
target     = OBSERVED
authority  = OBSERVED
policy     = OBSERVED
evidence   = OBSERVED
        |
        v
CONTINUE   (only when unchanged)
```

That positive result remains fixture-scoped.

```text
Fixture CONTINUE != Production CONTINUE
Observed Fixture Digest != Source Authenticated
```

Source-specific production adapters remain future work.
