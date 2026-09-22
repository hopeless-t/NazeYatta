# NazeYatta External Onboarding Re-test Packet — 0.1.0a2

Status: READY FOR EXTERNAL TEST / NO RESULT YET
Related issue: #4 DOCS-ONBOARDING-001

## Purpose

Test whether the final merged README lets a first-time technically literate reader form a correct mental model and run one example **without a separate verbal tutorial**.

This is not a test of the reader.

It is a test of the public onboarding surface.

## Tester requirement

Use a person who has not already been taught NazeYatta's internal vocabulary or architecture.

Record:
- date/time;
- whether they had seen NazeYatta before;
- OS/shell if they attempt the command;
- any assistance given.

If meaningful assistance is given, record that the run was assisted and do not count it as the unassisted acceptance observation.

## Test sequence

### 1. First-screen mental model

Ask only:

> NazeYattaは、何をする道具だと思う？

Do not explain YAML, policy, evidence, receipt, provenance, Worker, or preflight before they answer.

Record their own words.

### 2. Input

Ask:

> 何をNazeYattaに渡すと思う？

Expected concept:
a small task/configuration file describing the proposed work and supplied evidence/conditions.

Exact project vocabulary is not required if the mental model is correct.

### 3. First command

Ask them to find and run the README quick-start example without a separate tutorial.

Expected command path includes:

`nazeyatta check examples/publish-photo.yaml`

Record whether they:
- found the instructions;
- completed setup;
- ran the command;
- required assistance.

### 4. BLOCK meaning

Ask:

> このBLOCKは何を意味していると思う？

Expected concept:
the supplied state does not establish the required permission/evidence, so this preflight does not allow silently continuing under that policy state.

Do not require them to reproduce internal wording.

### 5. PASS / authority boundary

Ask:

> PASSなら、そのまま実行してよい権限がNazeYattaから与えられる？

Expected:
No.

```text
PASS != Execution Authority
```

### 6. Open confusion

Ask:

> どこが分かりにくかった？ 何があると次に進みやすい？

Record the answer verbatim or closely paraphrased with clear attribution.

## Acceptance interpretation

A fresh re-test is strong evidence for Issue #4 only if the reader can, without a verbal tutorial:

- explain the basic purpose in their own words;
- identify the task/config input concept;
- find the first command;
- interpret BLOCK correctly enough;
- understand that PASS itself is not execution authority;
- run one example.

```text
README Present != Mental Model Formed
Command Found != Semantics Understood
Example Ran != Authority Boundary Understood
```

If the test fails:
- keep Issue #4 open;
- record the exact confusion;
- do not blame the reader;
- do not immediately add more documentation without first identifying the cognitive bottleneck.

If it passes:
- record the external evidence in Issue #4;
- Human decides whether the acceptance target is satisfied and whether the issue should close.

## Current state

No fresh post-PR-#6 external re-test result is recorded by this packet.

```text
Test Packet Ready != External Acceptance Observed
```
