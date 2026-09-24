# Durable Receipt JSON File Contract

Status: bounded 0.2.x evidence-contract tranche.

NazeYatta already returns a typed `Receipt` and can print it to stdout with `--json`.
This contract adds an explicit reusable file output without changing receipt semantics.

## CLI

```bash
nazeyatta check examples/safe-read.yaml --receipt-out receipt.json
```

The command still prints the normal human-readable receipt unless `--json` is also requested.

The output file contains the existing Receipt object only. It does not add execution
authority, source qualification, freshness, signatures, or policy-authority claims.

## Serialization

Receipt files use:

- UTF-8;
- JSON;
- stable lexicographic key ordering;
- compact separators;
- one trailing newline;
- the existing receipt schema fields only.

The representation is deterministic for the same Receipt value.

```text
Deterministic Serialization != Cryptographic Authentication
```

This is a NazeYatta-local deterministic representation. It is not a claim of RFC 8785/JCS
compatibility.

## No clobber

`--receipt-out` creates a new file and refuses to overwrite an existing path.

```text
New Receipt != Permission To Replace Existing Evidence
```

A write failure returns a non-zero CLI error.

## Non-PASS receipts

A completed evaluation may write a receipt whether the outcome is `PASS`, `CAUTION`,
`REVIEW`, `EVIDENCE_REQUIRED`, or `BLOCK`.

This is intentional:

```text
Receipt = Evaluation Record
Receipt != PASS Claim
```

A `--require-lane` mismatch does **not** emit a file because the lane gate is a caller/CLI
condition that is not represented inside the Receipt object.

## Boundaries

```text
Receipt Persisted != Receipt Fresh
Receipt Persisted != Target State Bound
Receipt Persisted != Evidence Source Qualified
Receipt Persisted != Policy Legitimate
Receipt Persisted != Authority Granted
```

Freshness/target binding, evidence-source qualification, and policy authority remain separate
future contracts.
