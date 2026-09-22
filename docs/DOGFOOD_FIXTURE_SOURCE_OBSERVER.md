# Dogfood Fixture Source Observer v0.1

Status:

```text
TYPE = TEST / DOGFOOD ADAPTER
GENERIC SOURCE REGISTRY = NO
NETWORK = NO
WRITE = NO
SOURCE AUTHENTICATION = NO
```

## Purpose

Provide one truthful positive-runtime observation path for NazeYatta without building a general adapter framework.

An explicit JSON manifest maps a small fixed set of source refs to harmless local files.

Current refs:

```text
authority://dogfood/ci-safe-read-only
policy://dogfood/runtime-safe-read-v0-1
evidence://dogfood/fixture-exists
```

## Observation

For every requested source the observer:

1. requires the ref to exist in the manifest;
2. checks the manifest-declared source kind;
3. resolves the relative path beneath the fixed source root;
4. reads the actual bytes;
5. computes `sha256(bytes)`;
6. returns that digest as `binding_token`.

For evidence fixtures it also reads the evidence state from the JSON fixture and rejects unknown states.

```text
Read Actual Bytes = Observation Of Those Fixture Bytes
Observation Of Fixture Bytes != Source Authority Proven
```

## Filesystem boundary

The observer rejects:

- absolute/parent escape paths;
- resolved symlink escape;
- missing/non-file targets;
- unknown source refs;
- unsupported source kinds;
- oversized source/manifest files.

This is path bounding only.

```text
Bounded Fixture Root != OS Sandbox
```

## Why no generic registry?

The current requirement is only to learn whether the multi-bounce path can reach a truthful positive fixture-level CONTINUE.

Building a URI registry, network adapter layer, credential system, Git adapter, or PKI now would exceed the evidence for need.

```text
One Concrete Consumer Before Generalization
BUILD LESS / ROUTE BETTER
```

## Negative change test

A test copies the source fixtures, observes them, changes the copied policy fixture, observes again, and requires:

```text
RE_KY
POLICY_BINDING_CHANGED
```

This ensures the positive CONTINUE is not merely the result of injecting static tokens.
