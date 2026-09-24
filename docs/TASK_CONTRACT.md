# Runtime Task Contract

Status: bounded 0.2.x input-hardening contract.

NazeYatta evaluates policy selectors against fields inside a task. Missing structural fields must
not make a selector silently look inapplicable and thereby turn an incomplete task into `PASS`.

```text
Missing Structure != Safe
Failed Matching != DOES_NOT_APPLY
```

## Runtime-required structure

Before policy evaluation, the runtime requires:

- `task_id`: non-empty string;
- `action`: mapping;
- `action.operation`: non-empty string;
- `action.side_effect`: `none | write | external_write | destructive`;
- `action.externality`: `internal | public`;
- `semantics`: mapping;
- `semantics.critical_meaning_complete`: boolean;
- `evidence`: mapping;
- optional `worker` and `data`, if present, must be mappings;
- `schema_version: "0.2"` requires `evidence_records` to be a mapping.

A violation is an input error, not a policy finding:

```text
nazeyatta check incomplete.yaml
-> INVALID INPUT
-> exit status 3
```

## Why this is runtime validation instead of a new JSON Schema dependency

The repository contains JSON Schema artifacts, but current runtime semantics are not identical to
"reject everything a strict schema validator rejects".

For example, legacy evidence values intentionally normalize malformed/non-string values to
`INVALID` so policy can fail closed. Turning every such value into a parser error would be a
separate behavior change.

Therefore this tranche validates only the safety-critical structure needed before selector
matching. It does not claim that the runtime now performs complete Draft 2020-12 JSON Schema
validation.

```text
Runtime Task Contract != Full JSON Schema Enforcement
Schema File Present != Runtime Schema Validator Active
```

## Deliberately unchanged

This contract does not:

- validate every unreferenced Evidence Record;
- change legacy evidence-state normalization;
- authenticate Evidence producers;
- qualify Evidence sources;
- authenticate policy authority;
- bind receipt freshness or target state;
- grant execution authority.

```text
Task Structurally Valid
!= Evidence Verified
!= Policy Legitimate
!= Authority Granted
```
