# NazeYatta 0.1.0a2 — Release Notes Draft

Status: DRAFT / NOT PUBLISHED
Candidate source: `310aed9b588298ac17844ded516c8b86baed1f7d`

This draft is derived from the current CHANGELOG and observed release-readiness evidence. It does not authorize publication.

## Summary

0.1.0a2 hardens NazeYatta's alpha preflight evaluator and makes the first-run path easier to understand.

The main theme is conservative input handling:

```text
Malformed != Safe
Unknown != Verified
Evidence != Authority
PASS != Execution Authority
```

## Highlights

- adds the v0.2 provenance-input lane that links policy claims to Evidence Records;
- keeps legacy v0.1 scalar evidence as an explicit compatibility lane rather than treating it as provenance-qualified;
- rejects malformed or fail-open policy structures instead of silently weakening rules;
- rejects unsupported task schema versions instead of silently downgrading them;
- adds `--require-lane provenance-v0.2` so callers can refuse legacy scalar evidence;
- normalizes malformed input into explicit `INVALID INPUT` CLI failures instead of tracebacks;
- hardens human-readable receipt output against control-character / terminal-line injection;
- bounds oversized / deeply nested / non-finite YAML input;
- keeps package metadata, runtime version and receipt evaluator version aligned at `0.1.0a2`;
- simplifies English and Japanese README first-run onboarding while preserving evidence/authority boundaries.

## Current limits

0.1.0a2 is still an alpha preflight tool.

It does not implement:
- runtime observation;
- automatic end-to-end enforcement;
- autonomous remediation;
- producer/source authority authentication;
- an execution-authority grant;
- a universal policy engine.

The v0.2 Evidence Record lane validates structure/linkage/state. It does not prove that the observer is truthful or authorized to assert the claim.

## Technical verification

Observed 2026-09-22:

```text
source tests = 54 passed
wheel build = PASS
sdist build = PASS
fresh wheel install Python 3.11 = PASS
fresh wheel install Python 3.12 = PASS
canonical BLOCK behavior = PASS
canonical PASS behavior = PASS
package/runtime/receipt version parity = PASS
```

Built candidate artifacts:

```text
11b3c73df0dbb886ac5eaf8048a40d4b51fcd16bd8984c07fa560d9cb01c12c0  nazeyatta-0.1.0a2-py3-none-any.whl
8e53b7f923346c1564363dabe25ed3413a9fae2c60a37823f187a3c34fb53bf1  nazeyatta-0.1.0a2.tar.gz
```

See:
`docs/RELEASE_READINESS_0.1.0a2_2026-09-22.md`

## Publication gate

Human must separately decide:
- whether to publish this candidate;
- tag/release naming;
- whether to attach wheel/sdist artifacts.

PyPI publication is outside this draft.

```text
Release Notes Ready != Release Published
```
