# Runtime Dogfood: Fresh Safe-Read v0.2

Status:

```text
TYPE = PARTIAL RUNTIME DOGFOOD + FAIL-CLOSED RE-KY EXERCISE
GENERAL EXECUTOR = NOT IMPLEMENTED
SANDBOX = NOT CLAIMED
SOURCE-SPECIFIC OBSERVATION ADAPTERS = NOT IMPLEMENTED
POSITIVE RUNTIME CONTINUE = NOT CLAIMED
```

## Runtime path

```text
WorkerKYDeclaration
-> ValidationBaseline
-> KY Gate PASS
-> FreshHandoff
-> fresh Python subprocess
-> bounded read-only adapter
-> RuntimeExecutionReceipt
-> BoundaryObservation v0.2
-> Re-KY Gate
-> RE_KY
```

The final `RE_KY` is intentional.

The target path is actually observed by the read adapter, but authority/policy/evidence source bindings have no runtime adapters yet.

They are therefore represented as:

```text
observation_state = CARRIED_FORWARD
binding_token     = null
evidence state    = UNKNOWN
```

The Re-KY Gate correctly refuses `CONTINUE`.

## What the Fresh Worker receives

- serialized FreshHandoff;
- explicitly supplied allowed filesystem root.

It does not receive:

- WorkerKYDeclaration;
- ValidationBaseline;
- previous Worker reasoning;
- conversation history.

## Adapter boundary

The Worker accepts only `operation = read`.

The logical target must resolve beneath the allowed root. Parent traversal and symlink escape are rejected.

```text
Allowed Root Check != OS Sandbox
Fresh Process != Sandbox
```

No shell, write, delete, or network adapter exists.

## Runtime receipt

The receipt includes:

- task ID;
- handoff fingerprint;
- operation / target;
- SHA-256 content digest;
- byte count;
- before/after target identity fingerprints;
- Worker PID;
- outcome;
- `authority_granted = false`.

File contents are not included.

## Observation truth boundary

```text
target_identity               = OBSERVED
authority source              = CARRIED_FORWARD
policy source                 = CARRIED_FORWARD
evidence source               = CARRIED_FORWARD
source_bindings_observed      = false
reky_runtime_evaluated        = true
reky_runtime_outcome          = RE_KY
full CONTINUE claimed         = false
```

This is stronger than the v0.1 dogfood because the Re-KY path is now actually exercised without inventing source fingerprints.

```text
Runtime RE_KY PASS != Full Observation E2E
Ref Hash != Source Fingerprint
Carried Forward != Observed
```

## CI

The dedicated GitHub Actions dogfood job runs the orchestration on Python 3.11 after the normal 3.11 / 3.12 test matrix.

Negative runtime tests still cover:

- write rejection;
- parent traversal rejection;
- symlink escape rejection;
- unexpected handoff field rejection;
- no file-content leakage into receipt/log output.

## Next honest milestone

A future positive `CONTINUE` requires real source adapters (or another explicitly authorized source-observation mechanism) that can produce current binding tokens for authority, policy, and evidence sources.

Until then:

```text
Unobserved Critical Source -> RE_KY
```
