# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [0.1.0] - Unreleased

### Added

- `write-name-fragments` defaults also hold `multileg`, `close_position`, `close_all_positions`,
  `close_option_position`, `liquidat` and `exercise_option`, so `client-order-writes-name-retry` reads a multi-leg
  order, a position close, a liquidation and an options exercise as executing writes by default.
- `client-serde-imported-by-name` has fixtures for `headgate.pydantic` imported whole, as it does for `msgspec`.
- `client-order-writes-name-retry` skips a method named in `post-reads`: a read by POST (`search_orders`) is named
  like a read, so a fragment in its name no longer makes it a write.
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

- `headgate-verify`, a static checker for API clients written on headgate 0.7.0 or later: 32 ast-grep rules, six
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

- `one-class-per-host` no longer reports a comment inside a client class's bases list as a second base.
- A `pyproject.toml` that is not UTF-8, or cannot be read, is a usage error (exit 2) naming the file, not a traceback;
  `check_names` raises `ConfigError` for it.

The conventions were first worked out, and their client rules first written, for the author's own private API
clients; this release restates them against headgate's public API, with nothing of that project left in them.
