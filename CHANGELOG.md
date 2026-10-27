# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [0.1.0] - Unreleased

### Added

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

The conventions were first worked out, and their client rules first written, for the author's own private API
clients; this release restates them against headgate's public API, with nothing of that project left in them.
