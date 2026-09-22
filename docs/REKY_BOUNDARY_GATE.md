# Boundary Observation / Re-KY Gate v0.1

Status:

```text
TYPE = BOUNDARY-ONLY CHANGE DETECTOR
RUNTIME ADAPTER = NOT IMPLEMENTED
WORKER SPAWN = NOT IMPLEMENTED
AUTOMATIC RE-KY GENERATION = NOT IMPLEMENTED
AUTHORITY GRANT = NEVER
```

## Purpose

A Fresh Worker is allowed only one bounded execution bounce by the current handoff contract.

Before deciding whether another bounce may reuse the previous KY work, compare the execution boundary.

```text
Before BoundaryObservation
        +
After BoundaryObservation
        |
        v
CONTINUE / RE_KY
```

## What counts as a boundary?

This v0.1 experiment watches:

- target identity binding;
- authority reference/fingerprint;
- policy reference/fingerprint;
- evidence reference set;
- evidence state/fingerprint;
- observation source identity.

It deliberately does not hash the entire mutable target content.

```text
Target Content Changed
!=
Execution Boundary Changed
```

A successful intended write may change content without requiring a new KY by itself.

## CONTINUE

CONTINUE means:

```text
the observed boundary bindings did not change
between the supplied before/after snapshots
```

It does not authorize execution.

```text
CONTINUE != Execution Authority
Boundary Unchanged != World Unchanged
```

## RE_KY

RE_KY is returned when a relevant boundary changes, including:

- target identity changes;
- authority binding changes;
- policy binding changes;
- observation source changes;
- evidence is added/removed;
- evidence fingerprint changes;
- evidence state changes;
- evidence becomes STALE / INVALID / MISSING / UNKNOWN.

RE_KY only says the old KY/handoff should not be reused without another preflight cycle.

It does not generate a Worker automatically.

## Observation source boundary

An observation records who/what produced it, but this tranche does not authenticate or qualify that observer.

```text
Observed By X != X Qualified
Observation Present != Observation Trusted
```

Observer changes trigger RE_KY conservatively.

## Evidence states

A transition to one of these states requires Re-KY:

```text
STALE
INVALID
MISSING
UNKNOWN
```

The comparator does not invent a stronger state.

## Chronology and binding

Before/after observations must:

- use the same task ID;
- bind to the same Fresh Handoff fingerprint;
- be chronologically ordered.

Otherwise they are rejected as incomparable inputs rather than treated as a normal RE_KY event.

## Next stage

A runtime adapter may later produce BoundaryObservation records from real systems.

That adapter is not part of this tranche.

```text
Observation Contract Exists != Runtime Observation Exists
Re-KY Decision Exists != Re-KY Worker Spawned
```
