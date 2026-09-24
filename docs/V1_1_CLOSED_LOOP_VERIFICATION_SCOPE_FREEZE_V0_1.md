# NazeYatta 1.1 Closed-loop Verification Kernel — Scope Freeze v0.1

**Date:** 2026-09-25 (Asia/Tokyo)

**Status:** SCOPE FROZEN / HUMAN APPROVED

```text
NazeYatta 1.1 Scope Freeze != MVCA Main Line Authority
Catfood Research Finding != NazeYatta Product Authority
Scope Freeze != Execution Authority
VerificationReceipt != Action Authority
```

## 1. Product intent

NazeYatta 1.0 answers:

> Before this action happens, are the supplied checks satisfied?

NazeYatta 1.1 adds one bounded question:

> After an external caller acted, did the observed postcondition match the exact expected facts?

The product remains small, deterministic, embeddable, and non-executing.

The playful human-facing identity is intentional. A worker may correctly describe what it intends to do and still do something else. NazeYatta should make that mismatch visible without weakening the machine contract.

```text
Cute Presentation != Weakened Semantics
Playful Failure != Hidden Failure
Worker Self-Report != Verified Evidence
```

## 2. Frozen flow

```text
Task + Policy + Evidence
        |
        v
Preflight Receipt
        |
        v
external caller / executor owns the action
        |
        v
PostActionObservation
        |
        v
deterministic exact-fact verification
        |
        v
VerificationReceipt
```

NazeYatta does not execute the action.

## 3. Frozen input contracts

### 3.1 VerificationRequest

Required semantic fields:

```text
schema_version = "0.1"
classification = "POST_ACTION_VERIFICATION_REQUEST"
verification_id
task_id
preflight_receipt_fingerprint
task_fingerprint
action_fingerprint
target_binding
expected_facts
authority_granted = false
```

`target_binding` reuses the existing bounded target shape:

```text
kind
identifier
identity_fingerprint
```

`expected_facts` is a bounded map of normalized fact IDs to exact scalar expected values.

Initial v0.1 scalar value types:

```text
string
boolean
integer
```

No expression language is included.

### 3.2 PostActionObservation

Required semantic fields:

```text
schema_version = "0.1"
classification = "POST_ACTION_OBSERVATION"
observation_id
verification_id
task_id
preflight_receipt_fingerprint
task_fingerprint
action_fingerprint
target_binding
observed_facts
observed_by
observed_at
authority_granted = false
```

Each required observed fact has:

```text
observation_state = OBSERVED | UNKNOWN
value
```

Rules:

```text
OBSERVED -> value must be a supported scalar
UNKNOWN  -> value must be null
```

`observed_by` reuses the current observer categories:

```text
human
adapter
workflow
```

An observation records a claim about what was observed. It does not authenticate the observer.

## 4. Frozen output contract

### VerificationReceipt

Required semantic fields:

```text
schema_version = "0.1"
classification = "POST_ACTION_VERIFICATION_RECEIPT"
verification_id
task_id
request_fingerprint
observation_fingerprint
preflight_receipt_fingerprint
task_fingerprint
action_fingerprint
target_binding_fingerprint
outcome
reasons[]
authority_granted = false
retry_authorized = false
```

Frozen outcomes:

```text
VERIFIED_SUCCESS
VERIFIED_FAILURE
UNKNOWN
```

Frozen evaluation precedence:

```text
malformed input / identity-binding mismatch
    -> INVALID INPUT
    -> CLI exit 3

one or more exact observed contradictions
    -> VERIFIED_FAILURE
    -> CLI exit 2

no contradiction, but one or more required facts are UNKNOWN / not observed
    -> UNKNOWN
    -> CLI exit 2

all required facts OBSERVED and exact-match
    -> VERIFIED_SUCCESS
    -> CLI exit 0
```

A known contradiction outranks missing information:

```text
Observed Failure + Other UNKNOWN -> VERIFIED_FAILURE
```

## 5. Frozen exact-binding rules

The observation must bind exactly to the request for:

- verification ID;
- task ID;
- preflight Receipt fingerprint;
- Task fingerprint;
- action fingerprint;
- target binding.

Binding mismatch is not a postcondition failure. It means the verifier cannot truthfully claim that the artifacts belong to the same work item.

```text
Wrong Artifact != VERIFIED_FAILURE
Wrong Artifact -> INVALID INPUT
```

## 6. Frozen fact-comparison rules

The first tranche supports exact equality only.

Allowed:

```text
expected release_exists = true
observed release_exists = true
-> match

expected production_touched = false
observed production_touched = true
-> contradiction
```

Not included in v0.1:

- regex;
- numeric ranges;
- inequalities;
- contains/subset logic;
- custom predicates;
- semantic model judgment;
- temporal logic.

If a future consumer needs those, add them only through a later separately reviewed contract.

## 7. CLI surface

Add one additive command:

```text
nazeyatta verify REQUEST.yaml OBSERVATION.yaml
```

Supported projection flags should mirror the existing stable style:

```text
--json
--receipt-out PATH
```

The verification receipt file must use no-clobber behavior.

## 8. Human-facing playful projection

Machine outcomes remain exactly:

```text
VERIFIED_SUCCESS
VERIFIED_FAILURE
UNKNOWN
```

The human-readable CLI may project them playfully.

Target tone:

```text
✅😺 VERIFIED_SUCCESS
   expected and observed facts matched

🙀 VERIFIED_FAILURE
   NAZE YATTA?
   expected: production_touched = false
   observed: production_touched = true

🔎😿 UNKNOWN
   required fact was not observed
```

The playful projection must never:

- change the machine outcome;
- hide a mismatch;
- convert UNKNOWN into success;
- imply punishment, shame, or moral blame;
- imply execution or retry authority.

The joke is the mismatch between declared/expected intent and observed result, not humiliation of the worker.

## 9. First concrete consumer

The first consumer is NazeYatta's own release path.

The 1.0.0 release already produced a real bounded sequence:

```text
pre-write target observation
-> Human-gated external write
-> GitHub / PyPI public readback
-> exact commit / release-state / artifact-hash checks
-> public PyPI fresh-install smoke
```

The first 1.1 dogfood should encode release postconditions as exact facts and verify both:

- one positive exact-match case;
- one intentional mismatch case.

This prevents an abstract adapter framework from being invented without a consumer.

## 10. Required negative matrix

At minimum, tests must cover:

```text
V01 exact success
V02 observed value mismatch
V03 required fact UNKNOWN
V04 missing required observed fact
V05 verification_id mismatch
V06 task_id mismatch
V07 preflight_receipt_fingerprint mismatch
V08 task_fingerprint mismatch
V09 action_fingerprint mismatch
V10 target binding mismatch
V11 malformed observation state
V12 UNKNOWN with non-null value
V13 OBSERVED with unsupported scalar type
V14 duplicate / malformed fact identity
V15 request mutation changes request fingerprint
V16 observation mutation changes observation fingerprint
V17 observed contradiction + another UNKNOWN -> VERIFIED_FAILURE
V18 receipt authority_granted remains false
V19 receipt retry_authorized remains false
V20 receipt no-clobber output
```

## 11. Explicit non-goals

Do not add in this tranche:

- action execution;
- effect permits;
- automatic retry;
- rollback;
- queue / router / scheduler;
- worker lifecycle management;
- DecisionProvider / Jev / Cua / LLM calls;
- provider ranking;
- IAM / PKI;
- observer authentication;
- generic runtime adapter framework;
- expression DSL;
- policy generation or promotion;
- autonomous remediation;
- HCE economics fields;
- dashboard / SaaS.

## 12. Deferred lanes

Potential later work, only with a concrete consumer:

```text
DecisionProvider proposal lane
Run / Human-load economics sidecar
Bounded effect permit
Observed violation -> debrief routing
Stronger observer/source qualification
```

The existing Violation Debrief remains reusable. A `VERIFIED_FAILURE` may motivate a debrief, but verification itself does not invent a root cause.

```text
Observed Mismatch != Root Cause Proven
Worker Apology != Evidence
```

## 13. Compatibility rule

NazeYatta 1.1 is additive to the 1.x stable contract.

Existing 1.0 commands and meanings remain unchanged:

- `check`;
- `example`;
- `schema`;
- `debrief-template`;
- `--version`.

The new `verify` command must not reinterpret `PASS` or grant authority.

## 14. Borrowed principles / authority boundary

READ-ONLY prior art informed this freeze:

### MVCA Main Line

```text
Proposal != Decision
Decision Evidence != Action Authority
Unknown Effect Outcome != Permission To Retry
Replay != Re-execution
```

### Catfood Jev/Cua Lab

```text
Proposal != Authority
Decision != Verification
Execution Result != Postcondition
Request Check != Dispatch Currentness
```

### Harness Component Economics

```text
Attempt Success != Verified Success
Evidence Serialization != Semantic Verification
Possibly-effected UNKNOWN != Retry Permission
```

These principles were borrowed as design constraints only.

```text
Reference Access != Authority Transfer
Research Finding != Product Decision
```

## 15. Council / sensitivity result

100,000-run design sensitivity for the first 1.1 verification shape:

```text
Exact-fact verification kernel   100,000
Generic expression DSL                 0
Provider/plugin first                   0
Effect gate included                    0
```

100,000-run human-projection sensitivity:

```text
Neutral machine contract + playful CLI   100,000
Playful schema/outcome names                   0
Plain serious CLI                              0
```

These are design-sensitivity results under varied decision weights, not empirical product-success probabilities.

## 16. Freeze boundary

Frozen for the first 1.1 implementation tranche:

- three neutral verification outcomes;
- exact-fact comparison only;
- exact identity binding;
- UNKNOWN preservation;
- failure-over-unknown precedence;
- additive `verify` CLI;
- JSON + human projection;
- no-clobber verification receipt;
- playful CLI only, neutral machine contract;
- first-party release consumer dogfood;
- V01-V20 minimum matrix;
- no execution/retry authority.

Anything beyond this boundary requires a new Human-reviewed scope decision.
