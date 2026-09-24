# Schema / Runtime Parity Guard

Status: bounded 0.2.x drift guard.

NazeYatta ships JSON Schema artifacts and also has Python runtime validation. They are related,
but they are not the same mechanism.

```text
Schema Exists != Runtime Schema Enforcement
Runtime Validation Exists != Schema Automatically Updated
```

This guard checks only the subset that both surfaces intentionally share.

## Guarded Task contract

CI checks that `schemas/task.schema.json` agrees with the runtime Task Contract on:

- required top-level fields: `task_id`, `action`, `semantics`, `evidence`;
- required action fields: `operation`, `side_effect`, `externality`;
- non-empty `task_id` and `action.operation`;
- allowed `side_effect` values;
- allowed `externality` values;
- boolean `semantics.critical_meaning_complete`;
- optional `worker` and `data` being objects when represented by the schema;
- supported task schema versions;
- `schema_version: "0.2"` requiring `evidence_records`.

## Guarded Evidence contract

CI checks that the Evidence Record schema's `verification.state` enum matches the runtime
`EVIDENCE_STATES`.

It does **not** claim complete Evidence Record parity. Runtime provenance resolution also applies
claim linkage and timezone-aware timestamp checks.

## Guarded Receipt contract

CI checks that `schemas/receipt.schema.json` agrees with the emitted `Receipt` dataclass on:

- exact field set;
- receipt schema version `0.2`;
- outcome enum;
- evidence-lane enum;
- `authority_granted: false`.

## Intentional non-equivalence

This guard deliberately does not turn JSON Schema into the runtime validator.

Examples:

- legacy malformed scalar evidence may be normalized to `INVALID` by runtime rather than rejected
  as parser input;
- JSON Schema `format: date-time` is not treated as proof that runtime and every validator use
  identical timestamp semantics;
- schema `additionalProperties` choices are not automatically promoted into runtime rejection;
- unreferenced Evidence Records are not made authoritative or relevant just because a schema can
  validate them.

```text
Parity Guard != Full JSON Schema Enforcement
Shared Contract Match != All Semantics Identical
Schema Valid != Evidence Trusted
Schema Valid != Authority Granted
```

## Why CI instead of a new dependency

The shared invariants can be checked with the Python standard library and the project's existing
runtime constants/dataclasses. Adding a general JSON Schema runtime dependency would increase the
semantic surface and could accidentally change compatibility behavior.

If full runtime schema enforcement is proposed later, it requires its own parity/migration evidence.
