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

Install the `0.2.0a4` technical prerelease from PyPI and extract a packaged example:

~~~bash
python -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install "nazeyatta==0.2.0a4"

nazeyatta --version
nazeyatta example publish-photo > task.yaml
nazeyatta check task.yaml
~~~

The `example` command only copies a fixed bundled YAML example to stdout. It does **not** evaluate the task or grant execution authority.

For source development or contribution work, clone the repository instead; see [CONTRIBUTING.md](CONTRIBUTING.md).

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
nazeyatta example safe-read > safe-read.yaml
nazeyatta check safe-read.yaml
~~~

That example returns PASS.

The task input can also come from one bounded UTF-8 stdin stream:

~~~bash
nazeyatta example safe-read | nazeyatta check -
~~~

Here, `-` means Task YAML from stdin. It does not expand authority or change evaluation semantics, and `--policy -` is rejected so one stdin stream cannot ambiguously provide both Task and policy input.

You can extract the exact packaged copies of the existing core schemas too:

~~~bash
nazeyatta schema task > task.schema.json
nazeyatta schema evidence > evidence.schema.json
nazeyatta schema receipt > receipt.schema.json
~~~

Schema extraction is a transport/convenience surface only. It does **not** grant execution authority or add new schema semantics.

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
nazeyatta check safe-read.yaml --json
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

Implemented preflight foundation:

- deterministic YAML preflight evaluation;
- bundled generic baseline rules;
- explicit evidence states;
- conservative CLI exit codes;
- JSON and human-readable receipts;
- deterministic task/policy fingerprints;
- a provenance-linked v0.2 input lane;
- structured violation-debrief templates;
- tests and examples.

Bounded experimental contracts now also exist for:

- typed Worker KY declarations and a deterministic KY validation gate;
- a single-bounce Fresh Handoff and Boundary Observation / Re-KY comparison;
- fresh-process, read-only dogfood with local fixture source observation;
- BaselineDerivationRecord;
- a bounded dogfood DerivationSpec;
- a scoped SpecAdoptionRecord.

Those contracts and dogfoods demonstrate bounded mechanics. They do **not** turn NazeYatta into a production executor, authority system, IAM/PKI layer, or proof that a rule/spec is normatively correct.

Not automatic production end-to-end functionality:

- AI-generated Worker KY declarations;
- production source/runtime adapters and continuous observation;
- live execution enforcement;
- authority authentication for evidence, policy, or derivation-spec adoption;
- normative/semantic correctness proof;
- automatic remediation;
- authority generation.

~~~text
Fixture Dogfood != Production Runtime
RECORD_BOUND != Authority Authenticated
PROVENANCE_BOUND != Semantic Correctness Verified
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
