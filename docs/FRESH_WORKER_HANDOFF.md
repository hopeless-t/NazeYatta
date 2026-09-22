# Fresh Worker Handoff v0.1

Status:

```text
TYPE = SINGLE-BOUNCE HANDOFF CONTRACT
WORKER SPAWN = NOT IMPLEMENTED
RUNTIME EXECUTION = NOT IMPLEMENTED
OBSERVATION BINDING = NOT IMPLEMENTED
AUTHORITY GRANT = NEVER
```

## Purpose

After a Worker KY declaration receives a deterministic KY Gate PASS, compile only the bounded state needed by the next execution bounce.

```text
KY Worker
  -> WorkerKYDeclaration

KY Gate
  -> PASS

Handoff Compiler
  -> FreshHandoff

Fresh Worker
  -> future runtime consumer
```

The Fresh Worker should not inherit the previous Worker's reasoning transcript or full conversation.

## Why compile instead of passing the raw inputs?

Passing only the gate receipt is small, but forces the next Worker to re-interpret the baseline and the previous Worker's self-report.

Passing the raw KY declaration is also unsafe as a semantic shortcut because Worker self-report is not Evidence.

The compiled handoff therefore contains only a small boundary:

- intended action;
- admitted action scope;
- conservative forbidden scope;
- baseline-required hazard/control/stop IDs;
- source references;
- cross-stage fingerprints;
- single-bounce validity marker.

## Cross-stage binding

The compiler re-runs the deterministic KY Gate.

It rejects the handoff if:

- the supplied gate result is not PASS;
- the result does not exactly match recomputation;
- declaration fingerprint changed;
- baseline fingerprint changed;
- task/declaration/baseline IDs do not bind.

```text
Old PASS + Changed Input != Valid Handoff
Forged PASS != Valid Handoff
```

## Scope compilation

```text
admitted actions
  = Worker allowed actions
    INTERSECT
    Baseline allowed actions

forbidden actions
  = Worker forbidden actions
    UNION
    Baseline forbidden actions
```

The union for forbidden scope is intentionally conservative.

## KY content compilation

The handoff carries only baseline-required IDs for:

- hazards;
- controls;
- stop conditions.

Worker-only extra claims are not promoted into validated handoff truth.

```text
Worker Extra Concern != Baseline Requirement
Self-Report Detail != Validated Contract
```

## Authority boundary

The handoff copies source references but does not authenticate them.

```text
Authority Ref != Authority Proven
Policy Ref != Policy Authority Proven
Evidence Ref != Evidence Source Qualified
Fresh Handoff != Authority Grant
```

`authority_granted` is always false.

The surrounding Human/workflow remains responsible for actual execution authorization.

## Validity

The first handoff is explicitly:

```text
mode = single_bounce
runtime_state_bound = false
```

This means it is designed for one immediate execution bounce only.

It is not a reusable session credential and is not bound to later runtime observations.

```text
Single-Bounce Handoff != Eternal PASS
```

## Next stage

A future Observation Gate may bind:

- target identity;
- authority scope;
- policy version;
- evidence freshness;
- relevant runtime state.

When those bindings change, the system may require Re-KY before another execution bounce.

That observation/re-KY loop is not implemented here.
