# External First-Time Review Guide

Status: CURRENT FACILITATOR GUIDE  
Target public surface: NazeYatta `0.2.0a4` README / README.ja.md  
Purpose: collect first-time Human onboarding evidence for Issue #4.

> Do **not** send this guide to the tester before collecting their answers.
> Show only the public README surface they would normally encounter.

This is a lightweight usability check, not a certification, endorsement, or production qualification.

## What to show

Choose one:

- `README.md`
- `README.ja.md`

Do not explain the architecture, intended answers, Issue #4, Council conclusions, or internal project history first.

Helping the tester reach the README or run ordinary shell commands is fine. Explaining what NazeYatta is before they answer is not.

## Frozen questions

Ask these in order:

1. What do you think NazeYatta does?
2. What do you give it?
3. What command would you run first?
4. What does `BLOCK` mean?
5. Does `PASS` itself authorize execution?
6. What is still confusing?

Then, if practical, ask the tester to try the public 30-second path:

~~~bash
python -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install "nazeyatta==0.2.0a4"

nazeyatta example publish-photo > task.yaml
nazeyatta check task.yaml
~~~

The expected example result is `BLOCK` because publication permission is intentionally `UNKNOWN`.

## What counts as useful evidence

Record:

- which README language was used;
- whether the tester had seen NazeYatta before;
- answers to the six frozen questions;
- whether they attempted the example;
- whether the example ran successfully;
- any point where they became confused;
- any wording they interpreted differently from the maintainer's intent.

A short response is enough. Preserve the tester's own wording where possible.

## What does **not** count as the missing Human observation

These can improve the surface, but are not substitutes for a first-time Human:

- maintainer self-review;
- CI;
- pseudo-Council;
- Monte Carlo;
- another AI/model;
- screenshots or mockups alone.

~~~text
Better Surface != Human Comprehension Evidence
Technical Prerelease != Onboarding Accepted
~~~

## Acceptance interpretation

Do not grade the tester for matching exact project terminology.

The useful question is whether a first-time reader can reach the correct practical model:

~~~text
small task/evidence snapshot
-> NazeYatta evaluates supplied rules/evidence
-> PASS / REVIEW / BLOCK + receipt

PASS != execution authority
UNKNOWN != silently treated as safe
~~~

If the tester cannot explain that model or cannot identify what to run, treat the confusion as product/documentation evidence.

## Where to record the result

Add the observation to Issue #4:

`DOCS-ONBOARDING-001 — Make the first-run README obvious to a new user`

Include enough context to distinguish observed Human feedback from maintainer interpretation.

~~~text
External Feedback != Endorsement
Human Test Completed != Production Qualification
~~~
