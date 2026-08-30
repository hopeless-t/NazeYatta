# Changelog

## Unreleased

- reject fail-open policy bundles: `effect` / `on` values must be one of `CAUTION`, `REVIEW`, `EVIDENCE_REQUIRED`, `BLOCK` (a policy can no longer map missing evidence to `PASS`; typos such as `BLOCk` are a `PolicyError` instead of a `KeyError`)
- reject malformed rule selectors instead of silently applying the rule to every task (`when: {alll: …}`), require `in:` to be a list (a bare string did substring matching), and require `id` / `title` / `hazard` on every rule
- accept an unquoted YAML `on:` key (parsed as boolean `True` by YAML 1.1) so a forgotten quote cannot weaken a `BLOCK` rule or crash the fingerprint
- keep receipt fingerprints deterministic when YAML parses unquoted timestamps/dates (`observed_at: 2026-08-30T00:00:00+09:00`, policy metadata dates); a timezone-aware datetime object is provenance-qualified, a naive one is `INVALID`
- CLI: `--require-lane provenance-v0.2` fails (exit `2`) when a task resolves to the legacy scalar lane; malformed task/policy input exits `3` with `INVALID INPUT` instead of a traceback; receipts print on legacy Windows console code pages instead of raising `UnicodeEncodeError`
- add a v0.2 provenance task-input lane that resolves policy claim keys through Evidence Record IDs
- keep v0.1 scalar evidence as an explicit, receipt-visible legacy compatibility lane
- treat missing, malformed, mismatched, or non-normalized v0.2 records conservatively as `MISSING` or `INVALID`
- retain the invariant that evidence resolution never grants execution authority
- reject unsupported explicit task schema versions instead of falling back to legacy input
- align the receipt schema with emitted v0.2 receipts and validate provenance timestamps conservatively

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
