# KY / Runtime / Derivation Stack Integration Audit v0.2

Status:

```text
TYPE = MAIN-FACING REVIEW SURFACE
FEATURE LOGIC CHANGE = NONE
MERGE AUTHORITY = HUMAN
RELEASE AUTHORITY = HUMAN
```

## Stack under review

```text
#12 Worker KY declaration
-> #14 deterministic KY validation gate
-> #16 Fresh Worker handoff
-> #18 Boundary Observation / Re-KY gate
-> #21 Fresh-process safe-read dogfood
-> #23 observed / carried-forward / unknown source states
-> #25 fixture source observation + fixture-level CONTINUE
-> #30 BaselineDerivationRecord
-> #32 bounded dogfood DerivationSpec
```

Integration branch start point:

`63eaaaa7abc3aa661a132fff9b5aa63945f801cc`

Observed main at audit start:

`310aed9b588298ac17844ded516c8b86baed1f7d`

Compare at audit start:

```text
ahead_by = 90
behind_by = 0
```

## Previous integration surface

Draft PR #27 remains the pre-derivation integration snapshot.

This v0.2 surface extends review through the derivation provenance/spec tranches.

```text
#27 = pre-derivation snapshot
v0.2 = current derivation-aware snapshot
```

No previous PR is merged or closed by this audit.

## Current runtime evidence

Before this audit, the latest feature head had observed:

```text
Test #160 / run 35758625538

Python 3.11                  SUCCESS
Python 3.12                  SUCCESS
Runtime dogfood safe-read    SUCCESS
Baseline derivation dogfood  SUCCESS

140 passed in 2.18s
```

Safe-read dogfood maintains:

```text
fresh_process = true
source_bindings_observed = true
reky_runtime_outcome = CONTINUE
fixture_reky_runtime_continuation_observed = true
full_reky_runtime_continuation_claimed = false
authority_granted = false
```

Baseline derivation dogfood maintains:

```text
derivation_outcome = PROVENANCE_BOUND
transform_conforms_to_declared_spec = true
semantic_correctness_verified = false
production_baseline_compiler_claimed = false
authority_granted = false
```

## Truth boundaries

```text
Worker KY Self-Report != Evidence
KY Gate PASS != Execution Authority
Fresh Process != Sandbox
Fixture CONTINUE != Production CONTINUE

PROVENANCE_BOUND != Semantic Correctness Verified
Transform Matches Spec != Spec Is Normatively Correct

Integration CI PASS != Human Merge Acceptance
Merge != Release Publication
```

## Why stop feature expansion here?

The stack now spans the full bounded chain from Worker KY through runtime observation and derivation provenance.

The next unresolved question is normative authority over the declared derivation spec / policy semantics.

That is not something this integration audit should decide implicitly.

```text
More Code != More Authority
Recorded Spec != Legitimate Normative Spec
```

## Non-goals

Do not add in this audit:

- derivation spec authority model;
- generic transform DSL;
- production source adapters;
- automatic Re-KY Worker creation;
- mandatory derivation gate;
- IAM/PKI;
- production deployment/release.
