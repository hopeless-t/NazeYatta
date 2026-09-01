# Roadmap

## v0.1-alpha (this seed)

- deterministic YAML task evaluation
- generic policy bundle
- explicit evidence states
- preflight receipt fingerprints
- violation-debrief template
- examples/tests
- bounded input-ownership contract: upstream Human / Planner / Task Specification / trusted Adapter supplies task semantics; Human / trusted Adapter / workflow-appropriate Evidence Source supplies evidence; Worker self-declaration is not evidence

## v0.2 candidates

- implemented alpha input lane: claim-to-Evidence-Record references with conservative effective-state resolution
- JSON Schema validation on CLI input
- explicit policy provenance metadata
- reusable receipt JSON files
- receipt freshness / target-state binding
- runtime gate adapter interface
- separate override / authority record
- violation event schema

## Research lane

- per-observer evidence-state ceilings
- evidence-source allow-lists / source qualification
- stronger task-semantics provenance
- cryptographic producer authentication where justified by a concrete integration
- candidate hazard discovery by LLM/human
- policy-compliance harness experiments
- `RULE_ACKNOWLEDGED_BUT_IGNORED` dataset
- worker qualification updates from observed violations

These are research or later implementation topics. They are not implied by the v0.1-alpha ownership contract and are not required merely to keep an input-provenance issue open.

## Deliberately deferred

- autonomous remediation
- autonomous policy generation/promotion
- universal risk scores
- dashboards/SaaS
- router integration
