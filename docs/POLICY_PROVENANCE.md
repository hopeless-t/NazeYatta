# Policy Provenance Contract

Status: bounded 0.2.x policy provenance contract.

A policy bundle fingerprint proves which parsed policy content was evaluated. It does not by itself
say where that policy came from, who claims authority over it, or whether that authority is
legitimate.

```text
Policy Fingerprint Bound != Policy Legitimate
```

## Record

`PolicyProvenanceRecord` binds:

- provenance id;
- policy bundle id;
- policy reference;
- exact policy bundle fingerprint;
- source reference;
- source snapshot binding token;
- claimed authority reference;
- scope reference;
- lifecycle state;
- validity window;
- recorder identity metadata;
- record timestamp.

The record must explicitly keep these claims false:

```text
authority_authenticated = false
normative_correctness_verified = false
authority_granted = false
```

## Evaluation

`evaluate_policy_provenance(...)` checks:

- supplied policy bundle id;
- exact policy bundle fingerprint;
- expected policy ref;
- expected source ref;
- expected scope ref;
- ACTIVE / REVOKED lifecycle;
- valid_from / expires_at;
- optional current source snapshot token.

Possible outcomes:

```text
PROVENANCE_BOUND
PROVENANCE_NOT_ADMISSIBLE
SOURCE_CHANGED
```

`PROVENANCE_BOUND` means the record matches the supplied policy and current structural
expectations. It does not authenticate the claimed policy authority.

```text
PROVENANCE_BOUND != Authority Authenticated
PROVENANCE_BOUND != Normative Correctness Verified
PROVENANCE_BOUND != Execution Authority
```

## Bundled generic policy dogfood

Tests use the actual repository policy:

```text
policies/generic/rules.yaml
```

and freeze its current Git blob identity as the recorded source snapshot:

```text
gitblob:4e142217c2517534f3c42090abfd75958701a701
```

The current file's Git blob token is recomputed in tests. If the file changes, the recorded source
snapshot no longer matches until a deliberate provenance-record update is made.

This is change detection, not source authentication.

```text
Stable Git Blob != Trusted Policy Authority
Changed Git Blob != Policy Automatically Invalid Everywhere
```

The caller still decides which policy ref/source/scope it expects.

## Authority boundary

Current alpha does not independently establish that:

- the claimed authority ref identifies a real authority;
- that authority is entitled to set policy for the scope;
- repository maintainers are domain authorities;
- policy semantics are normatively correct.

Those require a concrete external governance/IAM/Human integration if and when one exists.

Do not infer:

```text
Repository Write Access
==
Domain Rule-Setting Authority
```
