# Security policy

## Reporting a vulnerability

Please report vulnerabilities privately through GitHub:
[Report a vulnerability](https://github.com/kelsayed17/headgate-client-skill/security/advisories/new). Do not open a
public issue.

Include what you found, how to reproduce it, and the impact you expect. You will get an acknowledgement within a
week, and a fix or a plan within 30 days for a confirmed issue.

## Supported versions

headgate-verify is pre-1.0: only the latest release receives fixes.

## Scope

headgate-verify reads client packages written by others, and the skill tells coding agents how to write them, so these
are in scope:

- `headgate-verify` or `headgate_verify.naming` importing, executing or evaluating any part of the code it checks, or
  reaching the network;
- a crafted client package, `docs_paths.json` or `[tool.headgate-verify]` table making the checker read or write
  outside the paths it was given;
- an instruction in the skill or its references that, followed as written, leads an agent to put a credential in a
  committed file, a recorded fixture, a cached response or a log;
- a rule that passes a client which sends a credential to a host other than the one it was meant for.

A rule that reports a correct client, or misses a broken one, is a bug: open an issue.
