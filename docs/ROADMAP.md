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

## v1.0 stable CLI core — target contract

The 1.0 target promotes the bounded command-line preflight core into the supported stable surface.

Canonical contract:
[STABLE_CORE_1_0.md](STABLE_CORE_1_0.md)

The stable 1.x surface includes:

- `nazeyatta check`, `example`, `schema`, and `--version`;
- bounded file/stdin Task input;
- fail-closed structural/input handling;
- deterministic policy evaluation;
- explicit evidence and outcome states;
- conservative exit codes;
- human-readable and JSON receipts;
- deterministic task/policy fingerprints;
- no-clobber receipt files;
- the provenance-v0.2 lane plus the legacy-v0.1 compatibility lane;
- Python 3.11 / 3.12 packaging from PyPI.

The following do **not** block 1.0:

- first-time Human onboarding acceptance under #4;
- generic normative-correctness proof under #28;
- universal runtime enforcement;
- IAM/PKI authority authentication;
- generic runtime adapters;
- violation-trace production;
- promotion of the bounded KY / FreshHandoff / Re-KY / derivation research contracts into the stable CLI guarantee.

```text
1.0 Stable CLI Core != Production Enforcement Platform
Stable Package != Authority System
PASS != Execution Authority
```

## Integration-bound HOLD items

Do not add generic framework code for these without a concrete consumer.

### Receipt freshness / target-state binding

The first-party GitHub Release / PyPI publication consumer has now exercised a concrete target mapping and real observation -> write -> readback path under completed Issue #54.

That establishes bounded evidence for that consumer. It does not create a universal freshness algorithm for unrelated consumers.

Future consumers should supply their own explicit runtime operation and target mapping rather than inheriting a generic assumption.

```text
Concrete Release Freshness Observed != Universal Freshness Guarantee
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

Issue #10 closed with the bounded authority decision: policy authority belongs to the relevant Human / team / organization and NazeYatta does not universally authenticate that authority.

NazeYatta records claimed authority references and scope/lifecycle metadata, but it does not decide which identity or governance system authenticates those claims.

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

That converged tranche is now the basis for the bounded 1.0 stable CLI contract. Stable 1.0 does not imply a universal production enforcement platform, authority authentication, or normative correctness proof.
