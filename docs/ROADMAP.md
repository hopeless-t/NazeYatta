# Roadmap

## v0.1-alpha

Implemented and published as the `v0.1.0a2` technical prerelease:

- deterministic YAML task evaluation;
- generic research-grade policy bundle;
- explicit evidence states;
- preflight receipt fingerprints;
- violation-debrief template;
- examples/tests;
- bounded input-ownership contract:
  - upstream Human / Planner / Task Specification / trusted Adapter supplies task semantics;
  - Human / trusted Adapter / workflow-appropriate Evidence Source supplies evidence;
  - Worker self-declaration is not evidence.

## v0.2 bounded contract tranche — converged core

Implemented on main:

- claim-to-Evidence-Record references with conservative effective-state resolution;
- deterministic no-clobber reusable receipt JSON files;
- fail-closed runtime Task structural contract;
- dependency-free JSON Schema / runtime parity guard for explicitly shared invariants;
- FreshHandoff + Boundary Observation / Re-KY contracts;
- reusable Boundary Observation construction and consumer-side validation;
- exact preflight/runtime artifact correlation record;
- BaselineDerivationRecord;
- bounded dogfood DerivationSpec;
- scoped SpecAdoptionRecord;
- explicit policy provenance record with source/scope/lifecycle binding.

These contracts intentionally preserve:

```text
PASS != Execution Authority
Worker Declaration != Evidence
Receipt Persisted != Receipt Fresh
Exact Artifact Correlation != Semantic Equivalence
Exact Artifact Correlation != Freshness
PROVENANCE_BOUND != Authority Authenticated
PROVENANCE_BOUND != Normative Correctness Verified
RECORD_BOUND != Authority Authenticated
```

## Integration-bound HOLD items

Do not add generic framework code for these without a concrete consumer.

### Receipt freshness / target-state binding

HOLD under #54.

Needed before resumption:

```text
exact generic Task semantics
-> explicit runtime operation mapping
-> explicit runtime target identity mapping
```

The current generic Task does not require a runtime target identity.

```text
Same task_id != Semantic Equivalence
No Concrete Mapping != Permission To Invent Freshness
```

### Runtime gate adapter

The core already exposes:

- `build_boundary_observation(...)`;
- `validate_boundary_observation_for_handoff(...)`;
- `evaluate_reky_gate(...)`.

A broader adapter interface should be driven by the first concrete runtime consumer rather than by an abstract framework requirement.

### Override / authority record

HOLD on #10's external authority boundary.

NazeYatta currently records claimed authority references and scope/lifecycle metadata, but it does not decide which identity or governance system authenticates those claims.

```text
Authority Attribution != Authority Authentication
NazeYatta != IAM
NazeYatta != PKI
```

### Baseline semantic / normative correctness

HOLD on #28 for a concrete real-domain verification model.

The current derivation chain can establish reproducibility and conformance to an adopted spec, but not that the spec itself is normatively correct.

```text
Transform Matches Spec != Spec Is Normatively Correct
```

### Violation event runtime

The repository currently has Violation Debrief documentation/schema but no observed-trace producer/consumer.

Do not equate a preflight policy finding with an observed runtime violation.

```text
Policy Finding != Observed Violation
```

Resume only when a concrete detector/trace consumer exists.

## Research / later integration lane

- per-observer evidence-state ceilings;
- evidence-source allow-lists / source qualification;
- stronger task-semantics provenance;
- cryptographic producer authentication where justified by a concrete integration;
- candidate hazard discovery by LLM/Human;
- policy-compliance harness experiments;
- `RULE_ACKNOWLEDGED_BUT_IGNORED` dataset;
- worker qualification updates from observed violations.

These are research or later implementation topics, not implied by the bounded core.

## Deliberately deferred

- autonomous remediation;
- autonomous policy generation/promotion;
- universal risk scores;
- dashboards/SaaS;
- router integration.

## Stop-build rule

```text
Roadmap Item Exists != Implement Now
No Concrete Consumer -> Do Not Add Generic Framework
BUILD LESS / ROUTE BETTER
```

The generic non-integration-dependent 0.2 contract tranche is considered converged at this boundary.

This does not imply a 0.2 release, production readiness, authority authentication, semantic correctness, or freshness verification.
