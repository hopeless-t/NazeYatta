# Runtime Dogfood: Fresh Safe-Read v0.3

Status:

```text
TYPE = BOUNDED FIXTURE RUNTIME DOGFOOD
GENERAL EXECUTOR = NOT IMPLEMENTED
SANDBOX = NOT CLAIMED
DOGFOOD FIXTURE SOURCE OBSERVATION = IMPLEMENTED
PRODUCTION SOURCE OBSERVATION = NOT IMPLEMENTED
GENERAL RUNTIME CONTINUE = NOT CLAIMED
```

## Purpose

Exercise the current multi-bounce path end to end with deliberately harmless local fixtures:

```text
Worker KY
-> deterministic validation
-> FreshHandoff
-> fresh safe-read subprocess
-> runtime receipt
-> source observations before/after
-> Re-KY Gate
-> CONTINUE
```

The positive `CONTINUE` is intentionally limited to fixed dogfood fixtures.

```text
Fixture CONTINUE != Production CONTINUE
CONTINUE != Execution Authority
```

## Fresh Worker execution

The execution Worker receives only:

- serialized FreshHandoff;
- explicitly supplied allowed filesystem root.

It does not receive:

- WorkerKYDeclaration;
- ValidationBaseline;
- previous Worker reasoning;
- conversation history.

The runtime adapter supports only:

```text
operation = read
```

Parent traversal and symlink escape outside the allowed root are rejected.

```text
Fresh Process != Sandbox
Allowed Root Check != OS Sandbox
```

No shell, write, delete, or network adapter is implemented.

## Dogfood source observation

The runtime baseline refers to:

```text
authority://dogfood/ci-safe-read-only
policy://dogfood/runtime-safe-read-v0-1
evidence://dogfood/fixture-exists
```

An explicit dogfood manifest maps only those refs to fixed local fixture files.

The fixture observer:

- accepts only manifest-listed refs;
- resolves paths beneath one fixed source root;
- reads the actual fixture bytes;
- computes SHA-256 over those bytes as the binding token;
- reads the evidence state from the evidence fixture;
- performs no write and no network operation.

```text
Manifest Entry != Source Authority
Observed Fixture Digest != Source Authenticated
```

This observer is a dogfood fixture adapter, not a generic URI/source framework.

## Before / after behavior

The fixture sources are observed once before the Fresh Worker runs and again after it finishes.

If their binding tokens and evidence state are unchanged, the Re-KY Gate may return:

```text
CONTINUE
```

A regression test changes a copied policy fixture between observations and requires:

```text
RE_KY
POLICY_BINDING_CHANGED
```

Thus positive and negative paths use the same observation mechanism.

## Runtime receipt

The execution receipt contains:

- task ID;
- handoff fingerprint;
- operation / target;
- SHA-256 content digest;
- byte count;
- target identity fingerprints before/after read;
- Worker PID;
- outcome;
- `authority_granted = false`.

File contents are not included.

## Claim boundary

A successful current dogfood may establish:

```text
fresh subprocess observed
bounded fixture read observed
target identity unchanged
configured local source fixture bytes observed before/after
Re-KY Gate evaluated
fixture-only CONTINUE observed
```

It does not establish:

```text
production source trust
authority authenticity
policy-authority legitimacy
evidence-source qualification
general executor safety
OS sandboxing
production CONTINUE
```

The output therefore keeps:

```text
fixture_reky_runtime_continuation_observed = true
full_reky_runtime_continuation_claimed = false
authority_granted = false
```

## CI

The dedicated `Runtime dogfood safe-read` GitHub Actions job runs after the normal Python 3.11 / 3.12 matrix.

The ordinary test suite also covers:

- write rejection;
- parent traversal rejection;
- symlink escape rejection;
- unexpected handoff-field rejection;
- no fixture-content leakage;
- unknown source-ref rejection;
- source-manifest traversal rejection;
- source-fixture symlink escape rejection;
- invalid evidence-state rejection;
- changed policy fixture -> RE_KY.
