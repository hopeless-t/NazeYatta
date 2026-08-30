# Semantics

NazeYatta separates normative rules, observations, authority, and presentation.

## Core distinctions

- Policy != Evidence
- Hazard != Violation
- Control != Evidence of Control
- Evidence != Authority
- Provenance Present != Authority Proven
- Evidence VERIFIED != Execution Authority
- Reviewer Label != Authenticated Reviewer Identity
- Rule Acknowledgement != Rule Compliance
- Worker Explanation != Root Cause
- Preflight PASS != Authority Granted
- Preflight PASS != Eternal PASS

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
