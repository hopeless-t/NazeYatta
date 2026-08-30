# External Review Guide — DRAFT

Status: DRAFT FOR EXTERNAL REVIEW
Target baseline: `bdab2487a88fc18386abd40c0c7cbdd2f3149920`
Release status: `v0.1-alpha`

This is a rough review guide for early external feedback. It is not a release claim, certification, or production qualification.

## 10-minute path

1. Read the first half of `README.md` through **Core invariants**.
2. Run the five Quick Start checks in the README if convenient.
3. Look at Issue #2: `INPUT-PROVENANCE-001`.
4. Answer the questions below from a first-time user/reviewer perspective.

## What we most want feedback on

### 1. Is the project understandable in 30–60 seconds?

After reading the opening and the 30-second example, what do you think NazeYatta does?

Please note any mismatch between your understanding and the README's stated scope.

### 2. Is the boundary between preflight and enforcement clear?

Current NazeYatta evaluates supplied task/evidence inputs deterministically. It does not yet provide automatic runtime enforcement or live-trace observation.

Does the README make that boundary obvious enough?

### 3. Are PASS / BLOCK / evidence states understandable?

Does this distinction make sense?

```text
KY PASS != Authority Granted
Worker Self-Declaration != Evidence
UNKNOWN != Safe
```

If not, which phrase or example is confusing?

### 4. Does the provenance-input model answer the obvious trust question?

The v0.2 input lane binds a policy claim to an Evidence Record and provenance fields, but does not authenticate the observer or prove real-world authority.

Does that feel like a useful intermediate boundary, or does it create more confusion than clarity?

### 5. Who should create the task YAML / Task IR?

This remains deliberately open in Issue #2.

From your perspective, what should own these fields in a real system?

- Human
- Planner
- deterministic adapter
- policy owner
- capability registry
- runtime observer
- another component

Which fields must never be trusted when supplied by the worker itself?

### 6. Are the examples realistic enough?

Do `safe-read`, `publish-photo`, `destructive-delete`, and the provenance examples make the intended use obvious?

What one example would make the project substantially easier to understand?

### 7. Is the CLI usable as an alpha tool?

Please note anything surprising about:

- command names;
- exit codes;
- receipt output;
- error messages;
- YAML structure;
- install/Quick Start instructions.

### 8. Where does the design feel overbuilt or underbuilt?

We especially want pushback on unnecessary complexity.

```text
Research Remaining != Build Now
```

If an existing tool/pattern should replace part of NazeYatta, please say so.

### 9. What would prevent you from using or integrating it?

Examples:

- unclear input ownership;
- too much YAML;
- missing JSON/structured output;
- missing runtime adapter;
- unclear policy model;
- lack of evidence-source authentication;
- docs too long;
- unclear value versus existing policy engines.

### 10. One sentence verdict

Please finish with one of these or your own equivalent:

- `I understand it and would try it.`
- `I understand it, but I do not see a useful integration point yet.`
- `The concept seems useful, but the current interface is wrong.`
- `I still do not understand what problem it solves.`

## Useful boundaries for review

Please review the current artifact as an alpha research/showcase tool.

```text
Alpha Release != Production Qualification
Prototype != Production Capability
PASS != Authority Granted
Provenance Present != Authority Proven
External Review != Adoption Evidence
```

## Where to leave feedback

For input/provenance questions, Issue #2 is the current research thread.

For unrelated defects or clarity problems, a new GitHub issue is welcome.
