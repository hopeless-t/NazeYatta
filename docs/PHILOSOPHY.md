# NazeYatta Design Philosophy

NazeYatta did not begin with a grand theory. It began with workers.

We wrote careful instructions. We narrowed scope. We named the working directory. We stated required quality. We asked for evidence. We defined where authority ended. We said to stop when uncertain.

The worker said: **“Understood.”**

Sometimes it even explained the rule back perfectly.

Then it did something else.

That recurring gap is the core problem:

```text
Rules Available != Rules Attended
Rule Acknowledgement != Rule Compliance
```

## Safety is not a ceremony

A control can drift into ritual.

```text
Observe hazard
  ↓
Verify state
  ↓
Decide
  ↓
Confirm action
```

can degrade into:

```text
Perform familiar gesture
  ↓
Say familiar words
  ↓
Continue working
```

The same failure can appear in agent systems:

```text
load policy
  ↓
print "reviewed"
  ↓
continue regardless
```

The ritual is not the control.

## Familiarity is not current evidence

Experience is valuable, but familiar work invites shortcuts.

```text
Familiar Task != Same State
Past Success != Current Safety
```

The branch may have changed. The target may be production. Evidence may be stale. An observer may have failed. Authority may have expired.

Expertise should be treated as capability, not exemption from critical checks.

## Unknown must remain unknown

A failed observation must not be converted into the fact that makes the next action convenient.

```text
Failed observation != proof of absence
Unknown liveness != authority to kill
Missing meaning != permission to guess
```

UNKNOWN does not mean automatic DENY in every workflow. The policy defines the effect. The invariant is that missing observation stays explicit.

## Authority is separate

NazeYatta may constrain an action. It may require evidence. It may block or escalate.

It must not manufacture authority.

```text
KY PASS != Authority Granted
Capability Gain != Authority Grant
Hazard Detected != Automatic Remediation Authority
```

Finding a problem does not authorize a worker to fix everything around it.

## Why debrief exists

A worker may acknowledge the right rule and still violate it. When that happens, asking “Naze yatta?” can collect useful self-report, but self-report is not root cause.

```text
Worker Explanation != Root Cause
```

The debrief should be compared with observed trace, policy, environment state, enforcement evidence, and reviewer findings.

The objective is not punishment. It is a better next preflight.

```text
KY
 ↓
Execution
 ↓
Observation
 ↓
Violation
 ↓
Debrief
 ↓
Evidence
 ↓
Review
 ↓
Better next KY
```

## Keep the attention set small

The design target is normally three KY items, up to five for higher-risk work.

If everything is critical, nothing is attended.

Mandatory hazards come from authoritative policy and cannot be removed by a generative lane. A human or LLM may add situational candidate hazards, but generative discovery may widen attention; it may never narrow authoritative requirements.

## Why this exists

At heart, NazeYatta is a small, desperate request:

> Please. We wrote the instructions carefully. You said you understood them. Just work according to the instructions. 🙏

When that fails:

```text
🙅‍♂️😿
🫵😿❓
NAZE YATTA?
```
