# Spec Adoption Record v0.1

Status:

```text
TYPE = SCOPED ADOPTION / AUTHORITY-ATTRIBUTION RECORD
AUTHORITY AUTHENTICATION = NOT IMPLEMENTED
NORMATIVE CORRECTNESS PROOF = NOT IMPLEMENTED
EXECUTION AUTHORITY GRANT = NEVER
```

## Purpose

Record that one exact derivation spec is attributed to one claimed authority reference for one bounded task/source scope and lifecycle.

```text
Exact DerivationSpec
+ Claimed Authority Ref
+ Exact Scope
+ Lifecycle
        |
        v
SpecAdoptionRecord
```

This is deliberately an attribution/adoption record, not proof of legitimate authority.

## Result language

The evaluator returns only:

```text
RECORD_BOUND
RECORD_NOT_ADMISSIBLE
```

It does not return:

```text
AUTHORIZED
APPROVED
TRUSTED
LEGITIMATE
```

because those words would exceed the current evidence.

## Scope

The v0.1 record binds:

- task ID;
- authority source ref;
- policy source ref;
- exact evidence source-ref set.

```text
Authority Somewhere != Authority Everywhere
Scoped Record != Global Authority
```

## Lifecycle

The record contains:

- ACTIVE / REVOKED status;
- valid_from;
- optional expires_at;
- explicit evaluated_at supplied to the evaluator.

The evaluator does not call wall-clock time internally.

```text
Explicit Evaluation Time -> Deterministic Result
```

## Bound result

`RECORD_BOUND` means only:

- exact spec ID/version/fingerprint match;
- exact expected scope matches;
- status is ACTIVE;
- evaluated time is inside the lifecycle window;
- the record itself does not claim stronger authority/correctness.

It still returns:

```text
authority_authenticated = false
normative_correctness_verified = false
authority_granted = false
```

## Dogfood authority reference

The example record uses:

`authority://dogfood/spec-adoption-owner`

This is a fixture-level claimed authority reference.

It is not authenticated and is not presented as a production organization authority.

```text
Claimed Authority Ref != Legitimate Domain Authority
```

## Truth boundaries

```text
Spec Adoption Record != Authority Authentication
Claimed Authority Ref != Legitimate Domain Authority
ACTIVE != Authenticated
RECORD_BOUND != Spec Normatively Correct
RECORD_BOUND != Execution Authority
```

## Why no GitHub approval / signature?

No concrete production integration currently justifies coupling domain authority to:

- repository maintainer status;
- GitHub PR review;
- signatures;
- PKI;
- organization IAM.

Those mechanisms may become appropriate for a specific integration later.

```text
Repository Maintainer != Domain Authority
Cryptographic Signature != Normative Authority
```

## Next remaining question

After this record, the unresolved problem is intentionally smaller:

> What concrete source authenticates that an `authority_ref` really has rule-setting authority for this exact scope?

That question remains outside this contract.
