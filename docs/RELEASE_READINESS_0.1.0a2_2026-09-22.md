# NazeYatta 0.1.0a2 Release Readiness Evidence — 2026-09-22

Status: TECHNICAL VERIFICATION PASS / RELEASE NOT PUBLISHED
Issue: #7 SHOWROOM-RECOVERY-001

## Authority boundary

Human authorized technical release verification and evidence preparation.

This evidence does **not** authorize:
- GitHub Release publication;
- PyPI publication;
- closing onboarding Issue #4;
- unrelated feature expansion.

```text
Verification PASS != Release Publication Authority
```

## Candidate identity

```text
repository = hopeless-t/NazeYatta
candidate source commit = 310aed9b588298ac17844ded516c8b86baed1f7d
verification branch = release/0.1.0a2-showroom-verify
successful verification instrumentation commit = 77fc43f8e187c90f408e82874bad3bc7620592b7
```

The verification workflow asserted that the candidate source commit is an ancestor and that the only delta from the candidate to the verification branch at execution time was:

`.github/workflows/release-verify.yml`

Product source was not changed for the successful verification run.

## GitHub Actions

Successful release verification:

```text
workflow = Release Verify 0.1.0a2
run = #3
run_id = 35724159524
conclusion = SUCCESS
```

Ordinary repository test workflow for the same verification head:

```text
workflow = Test
run = #28
run_id = 35724159595
conclusion = SUCCESS
```

Two earlier Release Verify runs failed because the temporary verification instrumentation incorrectly treated the branch HEAD / parent as the immutable source candidate. The product Test workflow passed on those commits. The assertion was corrected to verify source ancestry plus exact path delta before run #3.

```text
Verification Instrumentation Failure != Product Failure
```

## Source test suite

Release Verify run #3 build job:

```text
54 passed in 0.93s
```

## Built distributions

### Wheel

```text
filename = nazeyatta-0.1.0a2-py3-none-any.whl
size = 20602 bytes
sha256 = 11b3c73df0dbb886ac5eaf8048a40d4b51fcd16bd8984c07fa560d9cb01c12c0
```

### Source distribution

```text
filename = nazeyatta-0.1.0a2.tar.gz
size = 28799 bytes
sha256 = 8e53b7f923346c1564363dabe25ed3413a9fae2c60a37823f187a3c34fb53bf1
```

Build log reported:

`Successfully built nazeyatta-0.1.0a2.tar.gz and nazeyatta-0.1.0a2-py3-none-any.whl`

## Fresh wheel install

The built wheel was installed into fresh virtual environments from the workflow artifact.

### Python 3.11

```text
fresh wheel install = PASS
installed package version = 0.1.0a2
runtime __version__ = 0.1.0a2
receipt evaluator_version = 0.1.0a2
canonical publish-photo exit = 2 / BLOCK assertion PASS
canonical safe-read exit = 0 / PASS assertion PASS
authority_granted = false assertion PASS
```

### Python 3.12

```text
fresh wheel install = PASS
installed package version = 0.1.0a2
runtime __version__ = 0.1.0a2
receipt evaluator_version = 0.1.0a2
canonical publish-photo exit = 2 / BLOCK assertion PASS
canonical safe-read exit = 0 / PASS assertion PASS
authority_granted = false assertion PASS
```

Both text receipts were checked for:

`EXECUTION AUTHORITY: NOT GRANTED BY NAZEYATTA`

## Workflow artifacts

Observed artifacts from run #3:

```text
nazeyatta-0.1.0a2-dist
artifact_id = 10692444653
archive size = 49008 bytes
artifact archive digest observed by download step =
sha256:1106fc3b525e1f56511802b939d85f517abcea3aa4a60948a347a346345cbe77

nazeyatta-0.1.0a2-python-3.11-evidence
artifact_id = 10692785478
archive size = 1945 bytes

nazeyatta-0.1.0a2-python-3.12-evidence
artifact_id = 10692505959
archive size = 1945 bytes
```

Retention was configured for 7 days. Durable evidence is therefore this document plus GitHub Actions logs; the transient artifact itself must not be treated as the only durable record.

## Technical verdict

For candidate source commit `310aed9b...`:

```text
source tests = PASS
wheel build = PASS
sdist build = PASS
fresh wheel install Python 3.11 = PASS
fresh wheel install Python 3.12 = PASS
package/runtime/receipt version parity = PASS
canonical PASS behavior = PASS
canonical BLOCK behavior = PASS
authority non-grant invariant = PASS
```

Technical release readiness is established for the bounded checks above.

This does not establish:
- external onboarding acceptance;
- production enforcement;
- adoption;
- certification;
- runtime observation;
- release publication.

## Remaining showroom gates

1. fresh no-prior-context onboarding re-test for Issue #4;
2. Human release decision;
3. if approved, release metadata/tag preparation and publication;
4. CAT NOOD project-card refresh only after publication evidence.

```text
Technical Ready != Publicly Released
README Implemented != External UX Accepted
```
