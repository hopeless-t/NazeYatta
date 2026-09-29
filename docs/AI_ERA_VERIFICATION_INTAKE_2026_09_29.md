# AI-Era Verification Intake — 2026-09-29

> **Status:** RESEARCH INTAKE / NO PRODUCT BEHAVIOR CHANGE
> **Authority:** NONE

## Primary / first-party sources

1. Anthropic — *Automating eval design and hillclimbing with Claude*  
   https://claude.dev/blog/automating-eval-design-and-hillclimbing/
2. Knowledge Work — exploratory testing with AI  
   https://zenn.dev/knowledgework/articles/6996274de49607
3. Tabelog Tech Blog — AI requirements-definition workflow using staged questions  
   https://tech-blog.tabelog.com/entry/ai-requirements-definition-with-questions

## Atomic observations

### O1 — Improvement loops need held-out protection

Anthropic recommends evaluating iterative changes one at a time and using a held-out set to catch overfitting.

```text
Tuning-set Improvement
!=
Generalization Improvement
```

### O2 — Eval noise sets a minimum meaningful delta

Small score changes that are not larger than run-to-run variation are weak evidence for promotion.

```text
Observed Delta <= Noise Floor
-> REVIEW / MORE EVIDENCE
```

This maps naturally to NazeYatta's explicit PASS / REVIEW / BLOCK posture.

### O3 — Known checks and exploratory investigation are different jobs

The Knowledge Work practitioner report separates routine checking from exploratory testing and uses AI as an execution/recording partner while a human directs exploration.

```text
Repeatable Check
!=
Exploratory Search
```

### O4 — AI-generated questions need admission criteria

Tabelog reports that more than 50 generated questions were reduced to 8 currently blocking requirements questions by tagging stage and priority.

```text
Potential Check / Question
!=
Check Required Now
```

## NazeYatta transfer

The product should continue to distinguish:

```text
Evidence Collection
!=
Verdict

Preflight PASS
!=
Post-action Verification

Known Check
!=
Exploratory Investigation

Candidate Verification
!=
Required Verification
```

## Candidate future research

### VERIFY-SELECT-001 — minimum sufficient verification set

Given a change descriptor and risk class, compare:

1. all checks;
2. fixed smoke suite;
3. change-aware selected checks;
4. selected checks + escalation on uncertainty.

Measure:

- escaped failure rate;
- false BLOCK/REVIEW rate;
- execution time;
- compute cost;
- evidence completeness;
- replayability.

### EVAL-HOLDOUT-001 — policy/evaluator hillclimb discipline

For any future heuristic tuning:

- freeze train/tuning and held-out sets before optimization;
- change one policy component at a time;
- measure run variance;
- revert apparent wins that fail held-out evaluation.

## Claim ceiling

This note does not claim that fewer checks are safer or better by default.

The research question is whether a smaller **sufficient** verification set can preserve the safety/evidence floor while reducing cost.

No current NazeYatta rule, schema, verdict, or release behavior changes.

## Intake decision

**ABSORB as verification-research prior art.**
