## What changes

<!-- The behaviour this changes, for someone running headgate-verify or following the skill. -->

## Checklist

- [ ] `uv run ruff check`, `uv run ruff format --check` and `uv run ty check` pass, with no suppression comments
- [ ] `uv run python -m pytest --cov` passes, at or above the coverage floor
- [ ] A new or changed rule or check has fail and pass fixtures, written first and seen failing
- [ ] `uv run python scripts/gen_rule_docs.py --check` passes, and the skill's references describe the new behaviour
- [ ] `uv run headgate-verify examples/` passes with no findings
- [ ] `CHANGELOG.md` has an entry under "Unreleased"
