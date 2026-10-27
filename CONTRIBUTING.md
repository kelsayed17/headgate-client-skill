# Contributing

## Setup

headgate-client-skill needs Python 3.14 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Checks

Every change must pass all of these, which CI runs on every pull request:

```bash
uv lock --check
uv run ruff check
uv run ruff format --check
uv run ty check
uv run python scripts/gen_rule_docs.py --check
uv run python -m pytest --cov
uv run headgate-verify examples/
```

- **Lint and types are strict.** ruff selects every rule and ty treats every rule as an error. Fix the cause of a
  finding: suppression comments (`noqa`, `ty: ignore`, `pragma: no cover`) are not accepted.
- **Coverage never drops.** `--cov` fails below the `fail_under` floor in `pyproject.toml`. Raise the floor when you
  raise coverage; never lower it.
- **Docstrings** describe what the code does now and why, in the present tense.

## Rules and checks

- **Every rule and check has fixtures.** A rule lives in `src/headgate_verify/rules/<id>.yml`; its cases live in
  `tests/rules/<id>/fail/` and `tests/rules/<id>/pass/`, at least one of each. Write the fixtures first and watch them
  fail. `tests/test_rule_fixtures.py` fails for a rule with no fixtures and for a fixture directory naming no rule.
- **A rule says how to fix what it reports.** Its `note:` is printed under each finding and in
  `skills/building-headgate-clients/references/verifier.md`, which `scripts/gen_rule_docs.py` regenerates.
- **A correct client must pass.** Both worked examples under `examples/` pass with no findings; a change that makes
  either report a finding is either a regression or needs the example and the skill updated in the same change.
- **The skill matches the checker.** When a rule's behaviour changes, update the reference page that teaches it.

## Pull requests

Keep a pull request to one change, describe the behaviour it changes, and add an entry to `CHANGELOG.md` under
"Unreleased".
