# Changelog

## 1.1.0 — 2026-09-25 — stable release

- add the Human-approved Closed-loop Verification Kernel v0.1 scope;
- add neutral `VerificationRequest`, `PostActionObservation`, and `VerificationReceipt` contracts;
- add deterministic exact-fact outcomes `VERIFIED_SUCCESS / VERIFIED_FAILURE / UNKNOWN`;
- preserve exact work identity bindings and fail invalid binding mismatches as input errors;
- preserve `authority_granted=false` and `retry_authorized=false`;
- add `nazeyatta verify REQUEST OBSERVATION` with JSON and no-clobber receipt output;
- keep machine contracts neutral while projecting verification failures playfully in the human CLI;
- add captured NazeYatta v1.0.0 release facts as the first concrete verification dogfood;
- add V01-V20 coverage and built-wheel verification smoke;
- wire the Human-gated GitHub/PyPI release path for live self-dogfood: real preflight Receipt before publication, public readback, and verification by the exact re-downloaded PyPI wheel, while keeping publication and retry authority external.

```text
Cute Presentation != Weakened Semantics
VerificationReceipt != Action Authority
UNKNOWN != Permission To Retry
Observed Mismatch != Root Cause Proven
```

## 1.0.0 — 2026-09-25 — stable release

NazeYatta 1.0 promotes the bounded command-line preflight core to the stable supported surface.

- freeze the 1.x stable CLI contract for `check`, `example`, `schema`, and `--version`;
- support bounded YAML file/stdin input with fail-closed structural validation and conservative exit codes;
- support human-readable and JSON receipts, deterministic task/policy fingerprints, and no-clobber receipt files;
- support the provenance-v0.2 Evidence Record lane while retaining legacy-v0.1 as a compatibility lane;
- define Python 3.11 / 3.12 and PyPI packaging as the supported 1.0 package surface;
- separate bounded KY / FreshHandoff / Re-KY / derivation research contracts from the stable CLI guarantee;
- document that first-time Human onboarding evidence (#4) and generic normative-correctness research (#28) are useful but non-blocking for the bounded 1.0 core;
- add a stable/prerelease GitHub release channel while preserving manual dispatch, the Human `release` Environment gate, exact source binding, pre-write target observation, artifact hashes, and post-write readback;
- update public English/Japanese documentation and package metadata from alpha-prerelease wording to the bounded stable-core claim.

Important boundaries remain:

```text
Stable CLI Core != Production Enforcement Platform
Stable Package != Authority System
PASS != Execution Authority
Bundled Baseline != Universal Policy Authority
```

## 0.2.0a4 — 2026-09-25 — technical prerelease

Changes since `0.2.0a3`:

- add synthetic first-party GitHub Release and PyPI publication consumers that keep Human authority and publication permission explicit rather than inferring them from a PASS;
- bind the exact release Task target descriptor through the consumer projection into the runtime target observation, and reject target-defining Task drift without promoting generic semantic-equivalence or freshness claims;
- persist separate GitHub Release and PyPI publication workflows on canonical main, both manual-only and protected by the GitHub Actions `release` Environment;
- keep GitHub Release and PyPI as two distinct irreversible external-write boundaries with separate Human approvals, pre-write target observation, and post-write readback;
- preserve the existing PyPI Trusted Publisher workflow filename while constraining authentication to the `release` Environment;
- add release-workflow contract tests that fail if automatic publication triggers, the Environment gate, or least-privilege write/OIDC boundaries drift.

Important boundaries remain:

```text
PASS != Execution Authority
Environment Approval != Universal Authority Authentication
Exact Artifact Correlation != Freshness
Release Workflow Configured != Release Authorized
Technical Prerelease != Production Ready
```

## 0.2.0a3 — 2026-09-24 — technical prerelease

- allow one bounded UTF-8 Task YAML to be read from stdin with `nazeyatta check -`, while preserving the same 1 MiB input ceiling, structural validation, evaluation semantics, and exit codes as file input;
- reject `--policy -` explicitly so a single stdin stream cannot ambiguously supply both Task and policy documents;
- verify packaged-example-to-stdin pipelines, JSON receipt output, oversized stdin, and invalid UTF-8 fail-closed behavior.
- package exact copies of the existing core Task, Evidence Record, and Receipt JSON Schemas and expose them with `nazeyatta schema task|evidence|receipt` without adding new schema semantics.
- add a structured GitHub Concrete Integration Request form that collects the runtime operation, target identity, Task mapping, evidence producer, enforcement placement, and non-PASS behavior needed before held integration work can resume.

## 0.2.0a2 — 2026-09-24 — technical prerelease

- add packaged first-run task examples addressable as `nazeyatta example publish-photo` and `nazeyatta example safe-read`;
- keep example extraction separate from evaluation: the command prints fixed YAML only, while `nazeyatta check` retains its existing PASS/non-PASS exit semantics;
- bind packaged example bytes to the repository examples in tests so source and installed-package onboarding inputs cannot silently drift.
- add top-level `nazeyatta --version` aligned with package/runtime version metadata;
- add PyPI navigation metadata for Homepage, Repository, Issues, and Changelog, plus the continuously-tested Python 3.12 classifier.

## 0.2.0a1 — 2026-09-24 — technical prerelease

Current main includes the bounded post-`0.1.0a2` contract tranche:

- deterministic no-clobber receipt JSON files;
- fail-closed runtime Task structural validation;
- dependency-free schema/runtime parity guards for shared invariants;
- FreshHandoff, reusable Boundary Observation construction, and Re-KY integration;
- exact preflight/runtime artifact correlation with semantic-equivalence and freshness claims explicitly false;
- BaselineDerivationRecord, bounded DerivationSpec, and scoped SpecAdoptionRecord;
- policy provenance with source/scope/lifecycle binding while authority authentication and normative correctness remain explicitly unverified;
- roadmap convergence at the integration boundary: freshness, authority authentication, real-domain semantic correctness, and violation runtime remain HOLD until concrete consumers/evidence exist.

```text
0.2.0a1 Technical Prerelease != Production Ready
Core Converged != Production Ready
```

## 0.1.0a2 — 2026-09-24 — technical prerelease

- reorder the English and Japanese README so first-time users see what NazeYatta is, when to use it, one copy-paste example, result meaning, first-task YAML, field ownership, and the post-preflight flow before the deeper research material
- document the bounded v0.1-alpha input-ownership contract: task/action/data semantics come from an upstream Human / Planner / Task Specification / trusted Adapter; evidence comes from a Human / trusted Adapter / workflow-appropriate Evidence Source; Worker self-declaration is not evidence
- route stronger provenance/authority mechanisms such as observer ceilings, source qualification, authority records, runtime adapters, stronger task-semantics provenance, freshness binding, and cryptographic producer authentication to future research rather than treating them as solved
- reject fail-open policy bundles: `effect` / `on` values must be one of `CAUTION`, `REVIEW`, `EVIDENCE_REQUIRED`, `BLOCK` (a policy can no longer map missing evidence to `PASS`; typos such as `BLOCk` are a `PolicyError` instead of a `KeyError`)
- reject malformed rule selectors instead of silently applying the rule to every task (`when: {alll: …}`), require `in:` to be a list (a bare string did substring matching), require `exists:` to be an actual boolean, and require `id` / `title` / `hazard` on every rule
- accept an unquoted YAML `on:` key (parsed as boolean `True` by YAML 1.1) so a forgotten quote cannot weaken a `BLOCK` rule or crash the fingerprint
- keep receipt fingerprints deterministic when YAML parses unquoted timestamps/dates (`observed_at: 2026-08-30T00:00:00+09:00`, policy metadata dates); a timezone-aware datetime object is provenance-qualified, a naive one is `INVALID`
- CLI: `--require-lane provenance-v0.2` fails (exit `2`) when a task resolves to the legacy scalar lane; malformed task/policy input exits `3` with `INVALID INPUT` instead of a traceback; receipts print on legacy Windows console code pages instead of raising `UnicodeEncodeError`
- input boundaries: policy/task text printed in the human-readable receipt is sanitised (control characters, ESC sequences and line separators become U+FFFD, long fields are truncated) so a rule title can no longer forge `PASS` / `EXECUTION AUTHORITY` lines or rewrite the terminal; legacy scalar evidence is normalised conservatively (only ASCII strings are case-folded — `verıfıed`, full-width letters, padded or zero-width variants and non-string values are `INVALID`, not coerced by `str().upper()`); `accepted_states` and condition `field` are type-checked; task/policy files larger than 1 MiB, nested deeper than 64 levels, with more than 100k nodes or containing NaN/Infinity are rejected as `INVALID INPUT` instead of ending in `RecursionError`; `debrief-template` validates the rule id; a numeric `schema_version` gets a quoting hint
- add a v0.2 provenance task-input lane that resolves policy claim keys through Evidence Record IDs
- keep v0.1 scalar evidence as an explicit, receipt-visible legacy compatibility lane
- treat missing, malformed, mismatched, or non-normalized v0.2 records conservatively as `MISSING` or `INVALID`
- retain the invariant that evidence resolution never grants execution authority
- reject unsupported explicit task schema versions instead of falling back to legacy input
- align the receipt schema with emitted v0.2 receipts and validate provenance timestamps conservatively
- keep package metadata, runtime `__version__`, and default receipt `evaluator_version` aligned at `0.1.0a2`, with a regression test that fails on drift

## 0.1.0a1 — 2026-08-25

- first public NazeYatta OSS seed
- deterministic preflight rule evaluator
- generic 10-rule policy bundle
- evidence-state model
- receipt fingerprints
- structured “Naze Yatta?” violation-debrief template
- English and Japanese README
- beginner-oriented Japanese first-steps guide
- examples and tests
