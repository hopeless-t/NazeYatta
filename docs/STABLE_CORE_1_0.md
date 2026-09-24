# NazeYatta 1.0 Stable Core Contract

Status: TARGET CONTRACT FOR 1.0.0

NazeYatta 1.0 is the stable command-line preflight core.

It is intentionally smaller than the full research repository.

## Supported command-line surface

The 1.x compatibility promise covers:

```text
nazeyatta --version
nazeyatta check
nazeyatta example
nazeyatta schema
```

The stable core accepts bounded YAML Task input from a file or one UTF-8 stdin stream, evaluates the supplied task/evidence snapshot against the selected policy bundle, and emits a reproducible preflight result.

## Stable result semantics

Canonical outcomes:

```text
PASS
CAUTION
REVIEW
EVIDENCE_REQUIRED
BLOCK
```

CLI process meanings:

```text
exit 0 = PASS
exit 2 = valid evaluation, but outcome is not PASS
exit 3 = invalid input / policy / structural contract
```

A PASS is deliberately narrow:

```text
PASS = this supplied preflight snapshot passed the evaluated policy
PASS != execution authority
```

## Stable input and evidence surface

Supported evidence lanes:

- `provenance-v0.2` — supported provenance-linked Evidence Record lane;
- `legacy-v0.1` — compatibility lane for existing scalar evidence inputs.

The compatibility lane does not gain provenance guarantees merely by remaining supported.

Input handling remains fail-closed for malformed structures and bounded for file/stdin size, nesting, and node count.

## Stable output surface

The 1.x core includes:

- human-readable receipts;
- JSON receipts;
- deterministic task fingerprints;
- deterministic policy-bundle fingerprints;
- no-clobber receipt-file output;
- packaged Task, Evidence Record, and Receipt schema export.

Breaking changes to the documented 1.x CLI meanings or core schema semantics require a new major version. Additive compatible information may be introduced without changing the authority boundary.

## Packaging support

The 1.0 target supports:

- Python 3.11;
- Python 3.12;
- installation from PyPI;
- packaged first-run examples;
- packaged core schemas.

Release publication is separately Human-gated and is not part of evaluator authority.

## Bundled policy boundary

NazeYatta includes a generic baseline policy so the CLI can be run immediately.

That policy is a project-maintained baseline, not universal normative truth.

Real projects remain responsible for selecting policy appropriate to their domain and governance.

```text
Bundled Baseline != Universal Policy Authority
Rule Evaluation != Rule Authorization
```

## Not part of the 1.0 stable CLI guarantee

The repository also contains bounded research/integration contracts such as:

- Worker KY declarations and KY validation;
- FreshHandoff;
- Boundary Observation / Re-KY;
- BaselineDerivationRecord / DerivationSpec / SpecAdoptionRecord;
- policy provenance and consumer-specific runtime correlation experiments.

These may remain useful library or research surfaces, but 1.0 does not claim that they form a universal production runtime.

The following are explicitly outside the stable-core claim:

- execution-engine behavior;
- automatic end-to-end enforcement;
- IAM / PKI / authority authentication;
- universal normative-correctness proof;
- generic production runtime adapters;
- observed-violation trace production;
- autonomous remediation;
- autonomous policy generation or promotion.

## Non-blocking research and UX work

Issue #4 remains useful first-time Human onboarding evidence.

Issue #28 remains a real-domain normative-correctness research boundary.

Neither is required to establish the bounded 1.0 command-line contract.

```text
Stable CLI Core != Production Enforcement Platform
Stable Package != Authority System
External Human UX Evidence Pending != Core Semantics Unknown
Transform Matches Spec != Spec Is Normatively Correct
```

## Versioning rule

Within the 1.x line, preserve the documented stable CLI/result/input/output contract.

If a future change needs to invalidate those meanings rather than extend them compatibly, route that change to a new major version instead of silently changing the 1.x contract.
