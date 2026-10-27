# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [0.1.0] - Unreleased

### Added

- `headgate-verify`, a static checker for API clients written on headgate 0.7.0 or later: 32 ast-grep rules, six
  Python checks over a whole package (one class per host, no provider prefix on models, the package layout, one model
  flavour with its headgate extra, and two review warnings), each finding carrying how to fix it, allow comments with
  a required reason, `--format json`, and a `[tool.headgate-verify]` table for project lists. A path holding no client
  package is a usage error (exit 2), so a clean run always checked something.
- `headgate_verify.naming`, the method-name test helper: `endpoint_name`, `load_snapshot` and `check_names`.
- The `building-headgate-clients` skill and its Claude Code plugin manifest, with references for the conventions, the
  docs snapshot, method naming, testing and the generated rule list.
- Two worked examples that pass the checker: lda.gov (msgspec) and Open-Meteo (pydantic).

The conventions were first worked out, and their client rules first written, for the author's own private API
clients; this release restates them against headgate's public API, with nothing of that project left in them.
