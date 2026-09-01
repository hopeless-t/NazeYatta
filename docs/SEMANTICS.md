# Semantics

NazeYatta separates normative rules, observations, authority, and presentation.

## Core distinctions

- Policy != Evidence
- Hazard != Violation
- Control != Evidence of Control
- Evidence != Authority
- Document Author != Field Authority
- Producer Identity != Evidence Authority
- Worker Self-Declaration != Evidence
- Provenance Present != Authority Proven
- Evidence VERIFIED != Execution Authority
- Reviewer Label != Authenticated Reviewer Identity
- Rule Acknowledgement != Rule Compliance
- Worker Explanation != Root Cause
- Preflight PASS != Authority Granted
- Preflight PASS != Eternal PASS

## v0.1-alpha input ownership contract

NazeYatta v0.1-alpha evaluates a supplied task manifest. It does not create the task YAML and it does not infer missing authority from the identity of whoever wrote the file.

The bounded ownership contract is:

- task/action/data semantics are supplied by an upstream Human, Planner, Task Specification, or trusted Adapter;
- evidence assertions are supplied by a Human, trusted Adapter, or workflow-appropriate Evidence Source;
- the acting Worker must not manufacture its own `VERIFIED` facts merely because it wants to perform the action;
- NazeYatta evaluates supplied structure, claim linkage, evidence state, and policy effect;
- NazeYatta v0.1-alpha does not independently authenticate the real-world producer of those facts;
- NazeYatta v0.1-alpha does not independently prove that an evidence source has authority to assert a state;
- NazeYatta never grants execution authority from a preflight `PASS` alone.

```text
Task/action/data semantics
  <- upstream Human / Planner / Task Specification / trusted Adapter

Evidence assertions
  <- Human / trusted Adapter / workflow-appropriate Evidence Source

Acting Worker
  != authority to manufacture its own VERIFIED facts

NazeYatta
  -> evaluate supplied structure/linkage/state/policy
  != producer authentication
  != evidence-source authority proof
  != execution-authority grantor
```

The v0.2 provenance input lane improves structural traceability by binding a policy claim to an Evidence Record. Structural provenance is not itself proof of trust or authority.

Future mechanisms such as per-observer state ceilings, source allow-lists, authority records, runtime adapters, stronger task-semantics provenance, receipt freshness/target-state binding, or cryptographic producer authentication are separate research or implementation decisions. They do not change this v0.1-alpha ownership contract merely by being proposed.

## Observation states

Recommended evidence states:

- `VERIFIED`
- `PRESENT`
- `STALE`
- `INVALID`
- `MISSING`
- `UNKNOWN`

`UNKNOWN` must remain explicit. An observation failure must not be silently converted into absence, safety, or permission.

## Outcome states

- `PASS`
- `CAUTION`
- `REVIEW`
- `EVIDENCE_REQUIRED`
- `BLOCK`

Outcome is the policy effect of findings. It is not an observation state.

## Authority invariant

NazeYatta is restrictive, not authority-generative:

> NazeYatta may constrain authority; it may never manufacture authority.

A `PASS` only says the evaluated policy bundle produced no stronger blocking effect for the supplied snapshot.

## Generative hazard discovery

A future LLM/human discovery lane may add candidate hazards. Candidate hazards:

- may widen attention;
- may not remove authoritative controls;
- do not become policy automatically;
- do not grant authority.

`Repeated Concern != Policy Authority`.
