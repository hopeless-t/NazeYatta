# Baseline Derivation Dogfood v0.1

Status:

```text
TYPE = BOUNDED FIXTURE TRANSFORM DOGFOOD
PRODUCTION BASELINE COMPILER = NO
GENERAL POLICY COMPILER = NO
SEMANTIC CORRECTNESS PROOF = NO
```

## Why this is a separate dogfood

The pre-existing safe-read ValidationBaseline was created before the source-observation fixture files existed.

Creating a historical derivation record after the fact would falsely imply:

```text
old baseline
was derived from
later fixture snapshots
```

That is not claimed.

Instead this dogfood creates a **new baseline and its derivation record together** from the current fixture bytes.

```text
Current Fixture Bytes
-> bounded dogfood transform
-> new ValidationBaseline
+ BaselineDerivationRecord
```

## Bounded transform

The transform derives only semantics actually present in the fixtures.

```text
authority.allowed_action
-> baseline.allowed_actions

policy.forbidden_operations + policy.target
-> baseline.forbidden_actions
```

The current fixture sources do not define normalized KY hazard/control/stop requirements.

Therefore the dogfood deliberately produces:

```text
required_hazard_ids = []
required_control_ids = []
required_stop_condition_ids = []
```

```text
Missing Source Semantics != Permission To Invent Semantics
```

## Source snapshots

The dogfood reads the actual bytes of:

- authority fixture;
- policy fixture;
- evidence fixture.

It records SHA-256 of those exact bytes as source binding tokens.

The evidence state is read from the evidence fixture.

The generated BaselineDerivationRecord and new baseline are then passed to the deterministic derivation validator.

Expected result:

```text
PROVENANCE_BOUND
semantic_correctness_verified = false
authority_granted = false
```

## Meaning of PROVENANCE_BOUND

It means the new baseline, record, and source snapshots bind mechanically.

It does not mean the transform is normatively correct for a real organization.

```text
Dogfood Transform Deterministic
!=
Production Policy Semantics Correct
```

## Why no generic compiler?

This experiment has exactly one concrete consumer and one fixed fixture vocabulary.

Generalizing now into a policy language, LLM compiler, adapter registry, IAM layer, or domain compiler would exceed the evidence for need.

```text
Concrete Dogfood First
Generalization Later
BUILD LESS / ROUTE BETTER
```


## Machine-readable transform spec

The dogfood transform is now declared separately in:

`examples/dogfood-baseline-derivation-spec.json`

The v0.1 mapping vocabulary is deliberately fixed:

```text
allowed_actions_from = authority.allowed_action
forbidden_operations_from = policy.forbidden_operations
forbidden_target_from = policy.target

required_hazard_ids = []
required_control_ids = []
required_stop_condition_ids = []
```

The dogfood tool rejects any unsupported mapping and records the exact spec-file SHA-256 in its runtime summary.

```text
Transform Matches Declared Spec
!=
Declared Spec Is Normatively Correct
```

This is not a general transformation DSL.
