# Changelog

## Unreleased

- add a v0.2 provenance task-input lane that resolves policy claim keys through Evidence Record IDs
- keep v0.1 scalar evidence as an explicit, receipt-visible legacy compatibility lane
- treat missing, malformed, mismatched, or non-normalized v0.2 records conservatively as `MISSING` or `INVALID`
- retain the invariant that evidence resolution never grants execution authority

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
