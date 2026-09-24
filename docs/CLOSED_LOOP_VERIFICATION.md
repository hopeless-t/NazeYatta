# Closed-loop Verification — NazeYatta 1.1 development

**Status:** 1.1 development / main branch only / not included in the published PyPI 1.0.0 package.

NazeYatta 1.0 checks before an action.

The 1.1 development path closes one more small loop:

```text
Preflight
-> external caller acts
-> observe what actually happened
-> verify exact expected facts
```

NazeYatta still does not execute the action.

## Why this is NazeYatta

An AI can say the right thing and still do the wrong thing.

For example:

```text
AI before work:
  "I will update Preview only."
  "I will not touch Production."

Expected postcondition:
  production_touched = false

Observed after work:
  production_touched = true
```

The machine result is deliberately boring and precise:

```text
VERIFIED_FAILURE
```

The human CLI is allowed to be less boring:

```text
NAZEYATTA
👈😽 POST-FLIGHT VERIFY

🙀😿 VERIFIED_FAILURE

🙀 NAZE YATTA?
Observed facts contradicted one or more expected postconditions.

production_touched
  expected: false
  observed: true
  reason: FACT_MISMATCH

EXECUTION AUTHORITY: NOT GRANTED BY NAZEYATTA
RETRY AUTHORITY: NOT GRANTED BY NAZEYATTA
```

The joke is the mismatch. The machine contract does not become a joke.

```text
Cute Presentation != Weakened Semantics
Worker Self-Report != Verified Evidence
```

## Command

Development CLI:

```bash
nazeyatta verify request.yaml observation.yaml
```

Machine-readable output:

```bash
nazeyatta verify request.yaml observation.yaml --json
```

No-clobber receipt:

```bash
nazeyatta verify request.yaml observation.yaml --receipt-out verification.json
```

Exit codes follow the existing CLI convention:

```text
0  VERIFIED_SUCCESS
2  VERIFIED_FAILURE or UNKNOWN
3  invalid / mismatched verification input
```

## Outcomes

### VERIFIED_SUCCESS

Every required fact was observed and exactly matched the expected scalar value.

### VERIFIED_FAILURE

At least one required fact was observed and contradicted the exact expected value.

A known contradiction outranks unrelated UNKNOWN facts.

### UNKNOWN

No contradiction was observed, but at least one required fact was missing or not observed.

```text
UNKNOWN != Success
UNKNOWN != Permission To Retry
```

## Exact bindings

The request and observation must bind exactly on:

- verification ID;
- task ID;
- preflight Receipt fingerprint;
- Task fingerprint;
- action fingerprint;
- target binding.

A binding mismatch is invalid input, not a verified postcondition failure.

```text
Wrong Artifact != VERIFIED_FAILURE
Wrong Artifact -> INVALID INPUT
```

## Exact facts only

The first 1.1 tranche intentionally supports only exact scalar facts:

- string;
- boolean;
- integer.

It does not implement regexes, ranges, semantic model judgment, or expression DSLs.

## Authority boundary

NazeYatta verifies supplied observations. It does not authenticate the observer and it does not grant execution or retry authority.

```text
VerificationReceipt != Action Authority
Observed Mismatch != Root Cause Proven
```

If a failure deserves a "why did you do that?" review, the existing Violation Debrief can be used separately.

## First dogfood

The first concrete consumer is NazeYatta's own v1.0.0 release path.

The repository contains a deterministic dogfood that checks captured release facts such as:

- GitHub Release exists;
- `prerelease=false`;
- exact target commit;
- exact wheel SHA-256;
- public PyPI version.

It also intentionally flips one fact to prove the same kernel returns `VERIFIED_FAILURE`.

See:

```text
tools/dogfood_closed_loop_verification.py
```
