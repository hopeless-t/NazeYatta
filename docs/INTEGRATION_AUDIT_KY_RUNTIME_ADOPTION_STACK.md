# KY / Runtime / Derivation / Adoption Integration Audit v0.3

Status:

```text
TYPE = MAIN-FACING REVIEW SURFACE
FEATURE LOGIC CHANGE = NONE
MERGE AUTHORITY = HUMAN
RELEASE AUTHORITY = HUMAN
```

## Stack under review

```text
Worker KY declaration
-> deterministic KY validation
-> Fresh Worker handoff
-> Boundary Observation / Re-KY
-> fresh-process safe-read dogfood
-> observed/carried/unknown source states
-> fixture source observation + fixture-level CONTINUE
-> BaselineDerivationRecord
-> bounded DerivationSpec
-> scoped SpecAdoptionRecord
```

Integration branch start point:

`b873bd70eabb946ce05f2d800a676afdb3db2591`

## Latest observed verification before this audit

```text
Test #178 / run 35760683910
Python 3.11                  SUCCESS
Python 3.12                  SUCCESS
Runtime dogfood safe-read    SUCCESS
Baseline derivation dogfood  SUCCESS
151 passed in 1.96s
```

PR-trigger run #179 on the same head also completed SUCCESS.

## Current bounded runtime chain

```text
DerivationSpec
+ SpecAdoptionRecord
+ exact scope/lifecycle
        |
        v
RECORD_BOUND
        |
        v
bounded transform
        |
        v
BaselineDerivationRecord
        |
        v
PROVENANCE_BOUND
```

Observed false claims remain false:

```text
spec_authority_authenticated = false
spec_normative_correctness_verified = false
semantic_correctness_verified = false
authority_granted = false
```

## Authority boundary

The current alpha intentionally stops at:

```text
claimed authority_ref
+ exact scope
+ lifecycle
+ exact adopted-artifact binding
```

NazeYatta does not attempt to manufacture or universally authenticate organization authority.

A concrete integration may route authority authentication to:

- explicit Human approval;
- repository protected review;
- organization IAM/directory;
- signed authority record;
- external workflow contract.

```text
Authority Attribution != Authority Authentication
Repository Maintainer != Domain Authority
Cryptographic Signature != Normative Authority
```

## Why stop here?

The original product loop is about extracting a Worker's pre-work understanding and comparing it against independent rules/evidence before execution.

Building a universal identity/governance stack would move the product away from that bounded role.

```text
NazeYatta != Organization IAM
NazeYatta != PKI
NazeYatta != Universal Governance Platform
BUILD LESS / ROUTE BETTER
```

## Fingerprint boundary

```text
spec_fingerprint
= canonical parsed object fingerprint

spec_file_sha256
= raw artifact bytes digest
```

These are deliberately separate.

## Integration truth boundaries

```text
Worker Self-Declaration != Evidence
KY Gate PASS != Execution Authority
Fresh Process != Sandbox
Fixture CONTINUE != Production CONTINUE

RECORD_BOUND != Authority Authenticated
RECORD_BOUND != Spec Normatively Correct
PROVENANCE_BOUND != Semantic Correctness Verified

Integration CI PASS != Human Merge Acceptance
Merge != Release Publication
```

## Non-goals

This integration audit does not add:

- IAM;
- signatures/PKI;
- generic authority resolver;
- GitHub-review-as-authority coupling;
- production source adapters;
- automatic Re-KY Worker creation;
- mandatory adoption records in the KY Gate;
- production deployment/release.
