# Runtime Dogfood: Fresh Safe-Read v0.1

Status:

```text
TYPE = PARTIAL RUNTIME DOGFOOD
GENERAL EXECUTOR = NOT IMPLEMENTED
SANDBOX = NOT CLAIMED
SOURCE BINDING OBSERVATION = NOT IMPLEMENTED
FULL RE-KY RUNTIME CONTINUE = NOT CLAIMED
```

## Purpose

Exercise the first real runtime path without introducing a general execution engine.

The operation is intentionally boring:

```text
read one harmless fixture file
```

The runtime path is:

```text
WorkerKYDeclaration
-> ValidationBaseline
-> KY Gate PASS
-> FreshHandoff
-> fresh Python subprocess
-> bounded read-only adapter
-> RuntimeExecutionReceipt
```

The Fresh Worker receives only:

- serialized FreshHandoff;
- explicitly supplied allowed filesystem root.

It does not receive:

- WorkerKYDeclaration;
- ValidationBaseline;
- previous Worker reasoning;
- conversation history.

## Adapter boundary

The worker accepts only:

```text
operation = read
```

The logical target must be a relative path beneath the allowed root.

The adapter resolves the path before reading and rejects a path or symlink that escapes the allowed root.

```text
Allowed Root Check != OS Sandbox
Fresh Process != Sandbox
```

No shell command, write, delete, or network adapter is implemented.

## Receipt

The runtime receipt contains:

- task ID;
- compiled handoff fingerprint;
- operation / logical target;
- SHA-256 of file contents;
- bytes read;
- target identity fingerprints before/after the read;
- Worker process ID;
- outcome;
- `authority_granted = false`.

It deliberately does not include file contents.

## Fresh-process evidence

The dogfood orchestrator compares its own PID with the runtime receipt's Worker PID.

Different PIDs demonstrate a separate process was spawned.

```text
Different PID = Separate Process
Different PID != Security Sandbox
```

## Important observation limitation

This dogfood can directly observe the target path/file identity.

It cannot yet truthfully observe runtime fingerprints for:

- authority source;
- policy source;
- evidence sources.

FreshHandoff currently carries references to those sources, but no source-specific runtime adapter exists.

Therefore this tranche does **not** claim a positive full-runtime Re-KY `CONTINUE` result.

```text
Partial Runtime Dogfood != Full Observation E2E
Ref Hash != Source Fingerprint
Carried Forward != Observed
```

See #20 for the unresolved source-binding observation design.

## CI

The dedicated GitHub Actions dogfood job runs the orchestrator on Python 3.11 after the normal test matrix succeeds.

The normal Python 3.11 / 3.12 test matrix also includes negative runtime tests:

- write operation rejected;
- `..` escape rejected;
- symlink escape rejected;
- unexpected handoff fields rejected;
- file contents absent from runtime receipt/log output.

## Truth boundary

A successful dogfood demonstrates only:

```text
typed KY
-> deterministic validation
-> bounded handoff
-> separate-process fixture read
-> digest-only execution receipt
```

It does not demonstrate production filesystem safety, source authentication, general worker execution, or full Re-KY runtime observation.
