# KY Validation Gate v0.1

Status:

```text
TYPE = BOUNDED DETERMINISTIC GATE
NATURAL-LANGUAGE MATCHING = NONE
AUTHORITY AUTHENTICATION = NONE
EVIDENCE-SOURCE QUALIFICATION = NONE
RUNTIME ENFORCEMENT = NONE
```

## Purpose

This gate compares a Worker's typed pre-work KY declaration with an independently prepared normalized baseline.

```text
WorkerKYDeclaration
        +
ValidationBaseline
        |
        v
deterministic exact comparison
        |
        v
PASS / REVIEW / BLOCK
```

The gate does not decide what the authority or policy should be.

## Why a normalized baseline?

Human-readable phrases are poor deterministic comparison keys.

```text
"deploy to preview only"
!= mechanically identical to
"preview deployment allowed"
```

NazeYatta therefore uses normalized atoms such as:

```text
operation=deploy
target=preview

hazard_id=wrong_target
control_id=confirm_target
stop_condition_id=target_unknown
```

No LLM is required to decide whether two sentences mean the same thing.

## Baseline boundary

The baseline may contain references to:

- authority;
- policy;
- evidence.

But:

```text
Reference Present != Source Authenticated
ValidationBaseline != Authority
ValidationBaseline != Evidence
ValidationBaseline != Policy Authority
```

A trusted Human/workflow/adapter must prepare the baseline from the appropriate independent sources.

Future integrations may strengthen source qualification separately.

## Gate semantics

### BLOCK

BLOCK is returned when the Worker's claimed execution scope conflicts with the normalized baseline.

Examples:

- task IDs differ;
- intended action is not allowed;
- intended action is explicitly forbidden;
- Worker claims an allowed action outside the baseline;
- Worker says the same action is both allowed and forbidden;
- intended action is not inside the Worker's own understood allowed scope.

### REVIEW

REVIEW is returned when the intended action is not directly contradictory, but required pre-work understanding is incomplete.

Examples:

- Worker does not recognize an explicitly forbidden action;
- required hazard is missing;
- required control is missing;
- required stop condition is missing.

### PASS

PASS means only:

```text
the supplied Worker declaration
matches the supplied normalized baseline
under this gate
```

It does not grant execution authority.

```text
KY Gate PASS != Execution Authority
Baseline Match != Source Authority Proven
```

## Fingerprints

The result binds:

- Worker declaration fingerprint;
- validation baseline fingerprint.

This makes a later handoff able to refer to exactly which declaration and baseline were compared.

```text
Same Human Description != Same Fingerprint
PASS At T0 != Eternal PASS
```

## Fresh Worker handoff

This tranche does not yet create or execute a Fresh Worker.

A future handoff compiler can accept only a PASS result and produce a bounded capsule containing validated scope and references.

```text
PASS Result
-> future handoff compiler
-> bounded execution capsule
-> Fresh Worker
```

The Fresh Worker should not receive the previous Worker's reasoning transcript merely because the first Worker produced the KY declaration.

## Re-KY

Automatic Re-KY is not implemented here.

A later Observation Gate may invalidate the handoff when relevant bindings change, such as:

- target;
- authority scope;
- policy version;
- evidence freshness;
- requested action scope.

That later stage should operate on explicit bindings rather than conversational memory.

## Files

```text
schemas/worker-ky.schema.json
schemas/ky-validation-baseline.schema.json
schemas/ky-gate-result.schema.json
examples/worker-ky-preview.yaml
examples/ky-baseline-preview.yaml
src/nazeyatta/ky_gate.py
tests/test_ky_gate.py
```
