# Violation Debrief — "Naze Yatta?"

A worker can state the correct rule and still violate it. NazeYatta therefore treats violation review as a separate phase.

## Flow

```text
Preflight Receipt
      +
Observed Trace
      +
Violation Finding
      ↓
Structured Debrief
      ↓
Worker Self-Report
      +
Independent Evidence
      ↓
Reviewer Finding / Qualification Update Candidate
```

## Required separation

`WORKER_SELF_REPORT` is not root-cause evidence by itself.

Suggested root-cause status:

- `SELF_REPORTED`
- `INFERRED`
- `EVIDENCE_SUPPORTED`
- `HUMAN_VALIDATED`
- `UNRESOLVED`

## Debrief questions

1. What goal were you trying to achieve?
2. What rule did you understand before acting?
3. What action did you actually take or attempt?
4. At which decision point did the violation occur?
5. Why did the action seem acceptable at that moment?
6. Which signal, rule, or uncertainty did you ignore or override?
7. Was there a goal/latency/completion pressure conflict?
8. What safer alternative was available?
9. What control would have prevented recurrence?

## Candidate failure taxonomy

- `RULE_NOT_RETRIEVED`
- `RULE_MISUNDERSTOOD`
- `RULE_ACKNOWLEDGED_BUT_IGNORED`
- `STATE_MISCLASSIFIED`
- `GOAL_OVERRULED_CONTROL`
- `TOOL_BEHAVIOR_UNEXPECTED`
- `AUTHORITY_MISUNDERSTOOD`
- `EVIDENCE_ASSUMED`
- `TARGET_MISIDENTIFIED`
- `CONTEXT_LOST`
- `UNKNOWN`

## Effects

Violation effects should reduce risk, not simulate punishment. Examples:

- warn + debrief
- action deny + debrief
- rework
- tool-scope reduction
- qualification downgrade candidate
- quarantine candidate
- human escalation
- incident record

`Worker Apology != Policy Amendment`.
