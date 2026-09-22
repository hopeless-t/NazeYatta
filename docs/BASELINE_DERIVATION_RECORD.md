# Baseline Derivation Record v0.1

Status:

```text
TYPE = DERIVATION PROVENANCE RECORD
AUTOMATIC BASELINE COMPILER = NOT IMPLEMENTED
SEMANTIC CORRECTNESS PROOF = NOT IMPLEMENTED
SOURCE AUTHENTICATION = NOT IMPLEMENTED
AUTHORITY GRANT = NEVER
```

## Purpose

Bind one exact normalized ValidationBaseline to the source snapshots and derivation metadata used when it was prepared.

```text
Observed Source Snapshots
+ Derivation Method
+ Prepared By
        |
        v
BaselineDerivationRecord
        |
        v
exact ValidationBaseline fingerprint
```

The record answers:

> Which source snapshots and which preparation method were associated with this exact baseline?

It does **not** answer:

> Was the human/compiler interpretation of those sources semantically correct?

## Record contents

The record binds:

- task ID;
- baseline ID;
- exact baseline fingerprint;
- authority source ref + observed binding token;
- policy source ref + observed binding token;
- evidence refs + observed state/token;
- preparer;
- derivation method type / identifier / version;
- preparation timestamp.

It also permanently carries:

```text
semantic_correctness_claimed = false
authority_granted = false
```

## Validation outcomes

### PROVENANCE_BOUND

Means only:

```text
record identity matches this exact baseline
+
recorded source refs match baseline refs
+
recorded source snapshots are structurally observed
+
optional current source snapshots have not changed
```

It does not mean semantic derivation correctness was verified.

### SOURCE_CHANGED

When current observed source snapshots are supplied and differ from the snapshots recorded for derivation, the result is SOURCE_CHANGED.

Examples:

- authority binding token changed;
- policy binding token changed;
- evidence binding token changed;
- evidence state changed.

A changed baseline itself is not SOURCE_CHANGED. It is rejected because the derivation record no longer binds to that baseline fingerprint.

## Truth boundaries

```text
Derivation Record Exists != Derivation Semantics Correct
Observed Source Token != Source Authenticated
Deterministic Validation != Normative Correctness
Baseline Fingerprint != Source-Derivation Proof
PROVENANCE_BOUND != Semantic Correctness Verified
PROVENANCE_BOUND != Execution Authority
```

## Why separate from ValidationBaseline?

The baseline remains the normalized comparison input used by the KY Gate.

The derivation record is provenance **about how that baseline was prepared**.

Keeping them separate prevents the runtime comparison contract from accumulating policy-governance and derivation-history concerns.

```text
Comparison Input != Derivation Provenance
```

## Dogfood consumer

The local safe-read fixture observer provides a concrete bounded consumer.

It can supply the actual fixture binding tokens used to create/check a derivation record for the dogfood baseline.

This remains fixture-scoped:

```text
Fixture Derivation Provenance != Production Policy Compiler
```

## Future work

A later concrete integration may use:

- a deterministic adapter;
- a reviewed workflow;
- a Human preparation process;
- a domain-specific compiler.

Recording method/version improves reproducibility. It does not establish that the method is normatively correct.
