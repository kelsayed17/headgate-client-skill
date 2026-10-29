# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [0.1.0] - Unreleased

### Added

- A project rule (and any rule file) may carry `packages: [name, …]`: it runs only in the packages whose directory is
  named, rather than in every client package. The list must be non-empty; a rule with both `packages` and
  `skip-packages-in` runs where both allow it.
- `check_names` takes a method's call-shape prefix from its body: `walk_` for `self.paginate(...)`, `stream_` for
  `self.stream(...)` and `fetch_` for a verb call with `expect=as_bytes`, through a one-level delegate too. `get_`
  stays valid for every shape, and a `get_` and a `walk_` may read one path (a single page beside the whole walk), so a
  client keeps both without an override. `method-prefixes` in `[tool.headgate-verify]` lists the prefixes allowed
  (`[]` keeps every read `get_`), and `check_names` and `review_names` take `prefixes=`.
- Two `headgate-verify` rules: `client-wire-structs-are-frozen-without-gc` (a msgspec wire struct in `models.py`
  spells `frozen=True, gc=False`, and a subclass overrides neither) and `client-query-params-are-a-typeddict` (a query
  reaches the wire only as the enclosing function's own `**params: Unpack[...]`, untouched: not rebound or mutated,
  not merged, not handed to a collector leg as a keyword, not written into the path). The lda example's structs
  declare `gc=False`.
- `write-name-fragments` defaults also hold `multileg`, `close_position`, `close_all_positions`,
  `close_option_position`, `liquidat` and `exercise_option`, so `client-order-writes-name-retry` reads a multi-leg
  order, a position close, a liquidation and an options exercise as executing writes by default.
- `client-serde-imported-by-name` has fixtures for `headgate.pydantic` imported whole, as it does for `msgspec`.
- `client-order-writes-name-retry` skips a method named in `post-reads`: a read by POST (`search_orders`) is named
  like a read, so a fragment in its name no longer makes it a write.
- `rule-dirs` in `[tool.headgate-verify]` names directories of a project's own rules (`<id>.yml`, in the shipped
  rules' format), relative to that `pyproject.toml`. The command runs them beside the shipped rules, with their
  `note` as the fix, and an allow comment may name their ids. A missing directory, a file that is not valid YAML, a
  rule ast-grep refuses, a `.yaml` file, or an id a shipped rule, a check, a reserved id or another project rule
  holds is a usage error (exit `2`), before any package is read.
- `headgate-snapshot write <docs_paths.json> <url or file>` writes the docs snapshot from the vendor's OpenAPI or
  Swagger document (JSON, YAML, or `JSON.parse('…')` literals in a docs page bundle), and `refresh` reads each
  snapshot's `source` again. It sends a `User-Agent` naming the tool and an `Accept` preferring the OpenAPI media
  types, and dates the snapshot by the response's `Date` header.
- `check_names` names a method from the vendor's spec where the snapshot carries its `operationId`: the id's words
  the endpoint states (its path, the client's return models, the spec's schema names), the verb as the first word the
  endpoint does not state, a write's verb from the summary when the id's only repeats the HTTP verb, a namespace the
  spec's ids share stripped, a gate rejecting code paths, ids that write out the path and ids that spell a path hole,
  and a read's number from its path or a JSON-array answer. A colliding spec name keeps every id word, then takes the
  path's name. A write the spec names is held to that name. No word list is kept. `spec_name` and `spec_namespace`
  are public, for a caller with its own call-shape prefixes.
- `review_names` and the `headgate-names` command list the names no rule produces well (a rejected or colliding id, a
  write the spec does not name, a wordless path, two methods on one endpoint, a URL argument), for the skill's review
  step to name from the docs as overrides with a reason. It never fails.
- A snapshot endpoint carries the spec's operation details beside `verb` and `path`: `operation_id`, `summary`,
  `request_schema`, `response_schema` and `response_shape` (`array`, `object` or `""`). They are optional, so a
  snapshot scraped from docs pages still loads.

- Repository setup to match headgate's: a security policy, contributing guide and code of conduct; bug and feature
  issue forms and a pull-request template; weekly grouped Dependabot updates for uv and GitHub Actions; CI runs the
  tests with branch coverage (failing below the measured floor) and again at the lowest declared dependencies.

- `headgate-verify`, a static checker for API clients written on headgate 0.8.0 or later: 34 ast-grep rules, six
  Python checks over a whole package (one class per host, no provider prefix on models, the package layout, one model
  flavour with its headgate extra, and two review warnings), each finding carrying how to fix it, allow comments with
  a required reason, `--format json`, and a `[tool.headgate-verify]` table for project lists. A path holding no client
  package is a usage error (exit 2), so a clean run always checked something.
- `headgate_verify.naming`, the method-name test helper: `endpoint_name` and `check_names`, with the docs snapshot's
  schema in `headgate_verify.snapshot` (`load_snapshot`) and the static endpoint reader in `headgate_verify.endpoints`.
- The `building-headgate-clients` skill and its Claude Code plugin manifest, with references for the conventions, the
  docs snapshot, method naming, testing and the generated rule list.
- Two worked examples that pass the checker: lda.gov (msgspec) and Open-Meteo (pydantic).

### Fixed

- `client-method-shape` checks a walk's first request: a path string, or `PageRequest(<path>, body=<request
  parameter>, write=<WRITER>)`, its query only as `params=params`, with no `params=` or `idempotency_key=` beside a
  `PageRequest`. A computed path, a second positional argument or a `PageRequest` built any other way no longer
  passes.
- `client-method-shape` passes a stream, `async with self.stream(...) as <s>:` holding only
  `async for <c> in <s>.aiter_bytes(): yield <c>`, in an async def, which it used to report; the stream's keywords
  take the forward checks, with no body option, `expect=` or `cache_ttl=`.
- `one-class-per-host` no longer reports a comment inside a client class's bases list as a second base.
- A `pyproject.toml` that is not UTF-8, or cannot be read, is a usage error (exit 2) naming the file, not a traceback;
  `check_names` raises `ConfigError` for it.

The conventions were first worked out, and their client rules first written, for the author's own private API
clients; this release restates them against headgate's public API, with nothing of that project left in them.
