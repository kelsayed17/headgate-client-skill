# headgate-client-skill

A Claude Code skill, and the checker that goes with it, for building HTTP API clients on
[headgate](https://github.com/kelsayed17/headgate) the same way every time.

Given an API's docs, an agent following the skill saves the documented endpoints, writes one client class per host
with one one-line method per endpoint named after its path, records fixtures from the live API, tests the client
offline through its real headgate stack, and does not call the client done until the checker and the tests pass.

- **The skill**: [`skills/building-headgate-clients/SKILL.md`](skills/building-headgate-clients/SKILL.md), with its
  references (the conventions, the docs snapshot, method naming, testing, the rule list).
- **The checker**: `headgate-verify`, a Python package and command built on
  [ast-grep-py](https://ast-grep.github.io/). It reads a client package's source, never imports it and never touches
  the network, and reports each broken convention as `file:line rule-id message`.
- **Two worked examples** that pass it: [`examples/msgspec/lda/`](examples/msgspec/lda/) (msgspec, one host, paged
  reads) and [`examples/pydantic/open_meteo/`](examples/pydantic/open_meteo/) (pydantic, two hosts sharing one rate
  budget).

## Install the skill

As a Claude Code plugin, from this repository's own marketplace:

```text
/plugin marketplace add kelsayed17/headgate-client-skill
/plugin install headgate-client-skill@headgate-client-skill
```

or from a local checkout, for one session: `claude --plugin-dir path/to/headgate-client-skill`. The skill loads when
an agent is asked to build or change a headgate client. `SKILL.md` is plain Markdown, so another coding agent can be
pointed at it directly; the examples it links sit in this repository.

## Run the checker

The checker needs Python 3.14 or later, like headgate. Add it to the client project's dev dependencies and run it from
the project root:

```bash
uv add --dev headgate-verify
uv run headgate-verify src/your_clients/          # every client package under the path
uv run headgate-verify --format json src/         # for an agent or CI
```

Findings go to stdout, one per line as `<file>:<line> <severity> <rule> <message>` with the fix indented on the next
line; `checked N package(s)` goes to stderr. Exit `0` is clean (warnings allowed), `1` means at least one error, `2` a
usage error, including a path under which no client package is found. Project lists (packages allowed
a browser User-Agent, name fragments that mark an order-executing write) go in `[tool.headgate-verify]` in
`pyproject.toml`. The full rule list, configuration and allow-comment form are in
[`references/verifier.md`](skills/building-headgate-clients/references/verifier.md).

The method-name test helper ships in the same package: a client's `test_method_names.py` is
`assert check_names(client_py, docs_paths_json) == []` (`from headgate_verify.naming import check_names`).

## Develop

```bash
uv sync
uv run ruff check && uv run ruff format --check && uv run ty check
uv run pytest
uv run headgate-verify examples/
uv run python scripts/gen_rule_docs.py      # after changing a rule: rewrites references/verifier.md
```

Each rule has failing and passing fixtures under `tests/rules/<rule-id>/`.

## License

MIT. See [LICENSE](LICENSE).
