# Worker KY Bounce v0.1

Status:

```text
TYPE = BOUNDED CONTRACT EXPERIMENT
RUNTIME ENFORCEMENT = NOT IMPLEMENTED
KY GENERATION = NOT IMPLEMENTED
FIELD-TO-FIELD AUTHORITY COMPARISON = NOT IMPLEMENTED
```

## Purpose

NazeYatta originally grew from a simple operational idea:

before an AI Worker acts, make the Worker state what it thinks it is about to do, what scope it believes is allowed, what hazards it recognizes, and when it should stop.

That declaration is useful because it exposes the Worker's claimed understanding before execution.

It is not proof that the understanding is correct.

```text
WorkerKYDeclaration != Evidence
WorkerKYDeclaration != Authority
WorkerKYDeclaration != Chain of Thought
```

A later Validator may compare the declaration with independently supplied Authority, Policy and Evidence.

## Multi-bounce target flow

```text
KY Bounce
  Worker emits a short typed declaration
        |
        v
Validation Gate
  compare declaration with independent
  authority / policy / evidence
        |
        v
Fresh Execution Bounce
  a fresh Worker receives only a bounded
  handoff, not the previous Worker's reasoning
        |
        v
Observation Gate
  observe relevant state
        |
        +---- unchanged ----> continue bounded work
        |
        +---- changed ------> Re-KY before continuing
```

Only the first artifact — `WorkerKYDeclaration` — is implemented by this tranche.

## Why not capture reasoning?

The contract records externally useful claims:

- intended action;
- understood allowed scope;
- understood forbidden scope;
- recognized hazards;
- planned controls;
- stop conditions.

It deliberately does not ask for a reasoning transcript.

```text
Useful Boundary Statement != Hidden Reasoning
More Tokens != More Authority
```

The goal is to make the preflight declaration cheap, bounded and inspectable.

## Contract

Schema:

`schemas/worker-ky.schema.json`

Example:

`examples/worker-ky-preview.yaml`

Required atoms:

```text
declaration_id
task_id
classification = WORKER_SELF_REPORT
intended_action
understood_allowed_scope
understood_forbidden_scope
recognized_hazards
planned_controls
stop_conditions
declared_by
declared_at
```

The bounded statement arrays are intentionally small. They are not a place for a Worker to dump chain-of-thought.

## Evidence and authority boundary

The Worker declaration may say:

```text
"I understand that production is forbidden."
```

That only records the Worker's self-report.

Independent records still need to establish, where relevant:

- what Human/project authority was actually granted;
- which policy applies;
- what target was observed;
- which evidence source is qualified;
- whether evidence is current.

```text
Worker Says X != X Verified
Worker Understands Scope != Scope Granted
Worker Recognizes Hazard != Hazard Controlled
```

## Fresh Worker handoff

A future Validation Gate should compile a small handoff for the execution Worker.

The handoff should contain only bounded, externally useful state such as:

```text
task reference
validated allowed scope
validated forbidden scope
stop conditions
policy reference
authority reference
evidence / receipt references
target / freshness binding when available
```

Do not forward the previous Worker's hidden reasoning or entire conversation merely because it produced the KY declaration.

```text
Fresh Worker != Fresh Authority
Validated Handoff != Authority Grant
Previous Worker Reasoning != Handoff Contract
```

The execution Worker should still receive only the authority granted by the real authority source.

## Re-KY trigger candidates

Re-KY is future work, but likely trigger classes include:

- target identity changes;
- authority scope changes;
- policy version changes;
- evidence becomes stale or unknown;
- execution scope expands;
- a new hazard appears that is outside the validated declaration;
- an observation contradicts the handoff.

```text
PASS At T0 != PASS At T1
State Changed -> Previous KY May Be Stale
```

No automatic observation or Re-KY loop is implemented by this tranche.

## Presentation

The KY/猫 presentation may stay playful so repetitive preflight work is less tedious.

Presentation is not evidence.

```text
👈😽 ヨシ！ != Verified Safety
Playful UX != Weakened Semantics
```

## Next decision gate

Before implementing cross-field validation, gather a concrete consumer case that requires comparing:

```text
WorkerKYDeclaration
vs
Authority
vs
Policy
vs
Evidence
```

Then define the smallest deterministic comparison needed for that integration.

Do not add an LLM/Jev/Cua dependency merely to generate the declaration.
