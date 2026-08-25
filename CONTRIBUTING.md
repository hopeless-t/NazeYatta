# Contributing to NazeYatta

Thanks for taking a look at NazeYatta.

Code is not the only useful contribution. Documentation questions, confusing terminology, examples, tests, bug reports, and counterexamples are welcome.

NazeYatta is deliberately conservative about semantics. Before adding a feature or rule, preserve these boundaries:

- proposals do not become policy automatically;
- policy does not grant execution authority by itself;
- evidence is not authority;
- unknown observations stay unknown;
- self-reports are not root-cause evidence;
- generated hazards may add attention but may not remove mandatory requirements.

For rule contributions, include:

1. hazard statement;
2. applicability condition;
3. required evidence/control;
4. effect for missing/unknown/stale/invalid evidence;
5. at least one positive and one negative test case.

For documentation contributions, a simple statement like “I could not understand this term from the README” is useful evidence. Please open an Issue with the section and what was unclear.

Before submitting code:

```bash
python -m pip install -e .
pytest -q
```

Please do not include credentials, private customer/project data, or copied third-party material without clear redistribution rights.
