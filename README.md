# NazeYatta

[English](README.md) | [日本語](README.ja.md)

**NazeYatta is a small command-line preflight checker for AI workers and automation.**

It answers one narrow question:

> **Before this action happens, are the required checks actually satisfied?**

If the answer is not established, NazeYatta does not guess.

For example:

~~~text
Proposed action:
  publish this photo

Known facts:
  target checked                  VERIFIED
  worker capability              VERIFIED
  publication permission         UNKNOWN

Rule:
  public publication requires verified permission

NazeYatta:
  BLOCK
~~~

NazeYatta does **not** publish the photo.  
NazeYatta does **not** grant permission to publish it.

It only performs the preflight check and returns a reproducible result.

---

## The 30-second mental model

~~~text
Something wants to act
        |
        v
task snapshot + known facts
        |
        v
   NazeYatta
   checks rules
        |
        v
PASS / REVIEW / BLOCK
+ receipt of what was checked
        |
        v
a separate Human / Worker / Harness
decides or performs the actual action
~~~

Think of it as a **preflight checklist that a machine can evaluate**.

It is useful when you do **not** want:

~~~text
"I could not verify it"
        to become
"it is probably fine"
~~~

---

## Do I need NazeYatta?

Maybe not.

If one small script with one obvious if-statement solves your problem, use the if-statement.

NazeYatta becomes useful when you want several workflows or AI workers to share things such as:

- explicit UNKNOWN, MISSING, STALE, and VERIFIED states;
- reusable preflight rules;
- consistent CLI exit behavior;
- a receipt showing what was checked;
- a hard boundary between **evidence** and **permission to execute**.

Examples:

- before git push;
- before deleting or replacing something;
- before publishing content;
- before an external write;
- before using a capability that must be qualified;
- before acting on a target whose identity must be confirmed.

---

## Run one example

Requires Python 3.11+.

~~~bash
git clone https://github.com/hopeless-t/NazeYatta.git
cd NazeYatta
python -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -e .

nazeyatta check examples/publish-photo.yaml
~~~

The example says that publication permission is UNKNOWN.

The bundled baseline policy says public publication requires verified permission.

So the result is:

~~~text
NAZEYATTA
👈😽 PRE-FLIGHT KY

✋😾 BLOCK

NY-PUB-001  External publication requires verified provenance and permission
  hazard: PUBLICATION_WITH_UNKNOWN_RIGHTS
  evidence: publication_permission_verified = UNKNOWN
  effect: BLOCK

EXECUTION AUTHORITY: NOT GRANTED BY NAZEYATTA
~~~

Plain language:

> **"I cannot confirm that publishing is allowed, so this preflight will not treat it as OK to continue."**

Try a simple read-only example too:

~~~bash
nazeyatta check examples/safe-read.yaml
~~~

That example returns PASS.

But:

~~~text
PASS != Execution Authority
~~~

A PASS means this preflight found no stronger blocking effect for the supplied snapshot. It does **not** create permission by itself.

---

## What goes in?

For the first run, one small YAML task file is enough.

Example:

~~~yaml
task_id: MY-FIRST-READ

action:
  operation: read
  side_effect: none
  externality: internal

worker:
  required_capability: read_repository

semantics:
  critical_meaning_complete: true

evidence:
  worker_capability_qualified: VERIFIED
~~~

Save it as my-first-task.yaml, then run:

~~~bash
nazeyatta check my-first-task.yaml
~~~

NazeYatta ships with a small generic baseline policy, so you do not need to design a policy file just to run the first example.

At a high level, NazeYatta compares:

~~~text
what you want to do
+
what is currently known
+
the applicable rules
~~~

and emits a result plus a receipt.

---

## What comes out?

Current outcome types include:

- PASS
- CAUTION
- REVIEW
- EVIDENCE_REQUIRED
- BLOCK

Only PASS returns CLI exit status 0.

The result can also be emitted as JSON:

~~~bash
nazeyatta check examples/safe-read.yaml --json
~~~

The receipt includes fingerprints and evaluation information so another tool or Human can inspect what was evaluated.

---

## What NazeYatta is **not**

NazeYatta is not:

- the AI worker that performs the task;
- an execution engine;
- a permission-granting authority;
- a certification system;
- a complete policy platform;
- an autonomous remediation system;
- proof that the supplied evidence source was truthful or authorized;
- automatic end-to-end enforcement.

The current alpha evaluates supplied task/evidence structure and policy conditions deterministically.

For high-impact actions, use a separate enforcement point the worker cannot bypass.

---

## Why is it called "NazeYatta"?

**Naze yatta? / なぜやった？** means roughly:

> **"Why did you do that?"**

The project started from a recurring AI-worker failure mode:

~~~text
Human:
  "Do not do X."

AI worker:
  "Understood. I will not do X."

AI worker:
  does X
~~~

NazeYatta moves one part of that problem **before** the action:

> What had to be true before acting, and was it actually established?

The cat-heavy presentation is intentionally playful. The result semantics are not.

---

## Where the deeper ideas live

You do **not** need to understand these documents to run the first example.

Read them when you need the deeper model:

- [Semantics](docs/SEMANTICS.md) — Policy != Evidence, Evidence != Authority, states and invariants
- [Evidence Model](docs/EVIDENCE_MODEL.md) — Evidence Records, provenance linkage, freshness
- [Policy Model](docs/POLICY_MODEL.md) — applicability and policy effects
- [Threat Model](docs/THREAT_MODEL.md) — what the project assumes can go wrong
- [Roadmap](docs/ROADMAP.md) — implemented, research, and deliberately deferred work
- [Violation Debrief](docs/VIOLATION_DEBRIEF.md) — post-failure debrief structure
- [Japanese First Steps](docs/FIRST_STEPS.ja.md) — a more procedural Japanese introduction

---

## Current status

NazeYatta is an **alpha research tool**.

Implemented now:

- deterministic YAML preflight evaluation;
- bundled generic baseline rules;
- explicit evidence states;
- conservative CLI exit codes;
- JSON and human-readable receipts;
- deterministic task/policy fingerprints;
- a provenance-linked v0.2 input lane;
- structured violation-debrief templates;
- tests and examples.

Not automatic end-to-end functionality:

- task generation;
- runtime observation adapters;
- live execution enforcement;
- automatic provenance authentication;
- automatic remediation;
- authority generation.

~~~text
Unknown != Safe
Worker Self-Declaration != Evidence
Evidence != Authority
PASS != Execution Authority
~~~

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

If the repository is hard to understand, that is useful bug evidence. Please open an issue and describe where your mental model broke — even if the answer is simply:

> **"I do not know what I am looking at."**

## License

Apache-2.0. See [LICENSE](LICENSE).
