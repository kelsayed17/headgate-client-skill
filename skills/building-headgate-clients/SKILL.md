---
name: building-headgate-clients
description: Use when building, extending or reviewing an HTTP API client on headgate (the async Python HTTP client library) - a new provider's client package, a new endpoint, wire models, pagination or tests for one - or when headgate-verify reports a finding, a test_method_names.py or check_names fails, or a docs_paths.json snapshot needs writing.
---

# Building headgate clients

A headgate client is a thin, typed transport: one class per host, one one-line method per documented endpoint, wire
models that mirror the API's JSON, and offline tests that serve bodies recorded from the live API. This skill is the
procedure for building one, and `headgate-verify` is the gate it must pass.

## When to use

- Writing a client for a new API, or a new host of an API you already have a client for.
- Adding an endpoint, a model, a pager or a test to an existing headgate client.
- Reviewing a headgate client, or fixing what `headgate-verify` or the naming test reports.

Not for the layers above a client (services, caching of decoded results, mapping into your own domain types): the
client stops at the transport, and combining endpoints is its caller's job.

## The procedure

Do the steps in order. Each produces something the next one needs.

1. **Snapshot the docs.** Find the API's machine-readable surface (`llms.txt`, an OpenAPI document, a spec embedded in
   the docs site, or the docs pages) and save every documented verb and path as `docs_paths.json` beside the client.
   From an official OpenAPI or Swagger document, `headgate-snapshot write docs_paths.json <spec URL>` writes it.
   Read the API's terms before the first request and record what you measure. See
   [references/docs-snapshot.md](references/docs-snapshot.md).
2. **Pick the flavour and copy the matching example.** msgspec (`headgate[msgspec]`, `msgspec.Struct` models) or
   pydantic (`headgate[pydantic]`, `BaseModel` models); one per package. Start from this repository's examples, not
   from headgate's own `examples/` (which are API demos and break several rules here):
   - msgspec: [examples/msgspec/lda/](../../examples/msgspec/lda/), one host, 18 reads, a `NextUrl` page walk, a
     documented `404` read as `None`, a slow pace tested on a `TestClock`.
   - pydantic: [examples/pydantic/open_meteo/](../../examples/pydantic/open_meteo/), two hosts in one package (one
     class each), one `RateBudget` shared by both because the quota is per IP address.
   Add the ruff setting the models need (`runtime-evaluated-base-classes`) and the headgate extra; see
   [references/conventions.md](references/conventions.md#project-setup).
3. **Write the models, then the module-level values, then the methods.** Models first (`models.py`: wire shapes with
   the API's field names, and a `<Endpoint>Params` `TypedDict` per endpoint's query). Then, at module level of
   `client.py`: the base URL (a host with no path), the pace, every reader (`decoder(...)`, `Expect(...).on(...)`),
   any writer and retry policy; pagers and page budgets go in `pagination.py`. Then the class, whose methods are each one statement forwarding
   to a headgate verb or `paginate`. Write the module docstring as you measure: dates, statuses, error bodies, limits,
   terms, and what you did not measure. The full rules are in [references/conventions.md](references/conventions.md),
   and the method names in [references/naming.md](references/naming.md): the spec's `operationId` where the gate
   passes it, else the path.
4. **Record fixtures and write the tests.** Record one body per documented read and per documented error from the live
   API, politely and within its terms; trim lists and redact personal data. Test offline through the client's real
   headgate stack: `FakeTransport`, a `TestClock` for a paced client, syrupy snapshots, the request asserted, and a
   `test_method_names.py` that runs `check_names`. See [references/testing.md](references/testing.md).
5. **Run the gate:**

   ```bash
   uv run headgate-verify path/to/provider        # from the project root, where pyproject.toml is
   uv run pytest path/to/provider                 # or tests/provider/, wherever the tests live
   ```

   Fix every error. The rule list, the configuration and the allow-comment form are in
   [references/verifier.md](references/verifier.md).
6. **Review the names no rule produces well.** `uv run headgate-names path/to/provider/tests/test_method_names.py`
   lists them: a read named by its path because the spec's `operationId` was rejected or collided, a write the spec
   does not name, a wordless path, two methods on one endpoint, a method taking its URL as an argument. For each,
   read the docs; keep a name that says what the endpoint does, else propose one in the vendor's words and record it
   in `OVERRIDES` keyed `"VERB path"`, with a one-line reason, for the reviewer to judge in the diff. See
   [references/naming.md](references/naming.md#the-review-step-names-no-rule-produces-well).
7. **Resolve every warning in writing.** A warning (`client-except-needs-review`, `client-cache-with-bearer-auth`)
   does not fail the run, but a person has to judge it: fix the code, or keep it with an allow comment whose reason
   says why it is right (`# headgate-verify: allow <rule-id> -- <reason>`). Say how each was resolved when you report.

**Done** means `headgate-verify` prints nothing on stdout (every warning was fixed or carries an allow comment with a
reason) and exits `0`, and pytest passes, the naming test included. Not before: a client the verifier passes can still be
misnamed, and only the naming test catches that.

## Never

These are the mistakes that make a working client wrong. The verifier or the naming test fails every one but 5 and 7,
which are warnings a reader judges.

1. **Never merge two hosts into one class, or give two client classes a shared base class.** Each host has its own
   limits, outages and auth; one class per host keeps each base URL, budget and breaker honest, and shared code is a
   module-level function or value, never inheritance.
2. **Never fold several endpoints into one method** because a caller wants them together. One method per endpoint
   keeps each call testable against its docs; combining results is the caller's job.
3. **Never name a method after a docs heading** (`ticker_overview`). Names come from the spec's `operationId` or
   the path (`get_reference_ticker`), so anyone can find the method from the docs or the URL and the naming test can
   check it; a name the rules cannot give is an override with a reason.
4. **Never return `None` or a raw dict on failure.** Every call declares the responses it expects, and anything else
   raises a typed headgate error; `None` is only a documented answer (a `404` meaning "no such thing") or a write that
   returns nothing. A silent `None` hides an outage as an empty result.
5. **Never catch an error and quietly drop it.** A swallowed error turns a broken feed into missing data that nobody
   notices for weeks; a client method re-raises a more specific headgate error or does not catch at all.
6. **Never wrap a transport; subclass it.** A wrapper hides the inner transport from headgate's stack and from tests;
   a subclass calls `super().handle_async_request`.
7. **Never cache a bearer-authenticated response in a shared partition.** headgate's default
   `Partition.CREDENTIAL` keeps each credential's entries apart and never stores `Authorization`; `Partition.SHARED`
   serves one caller's response to another and is for public data only.
8. **Never prefix a model with the provider** (`LdaFiling`). The module path already says the provider; the prefix is
   noise in every signature.

## References

- [references/conventions.md](references/conventions.md): the conventions in full: the package, the class, methods,
  models, errors, pagination, rate budgets, the module docstring, project setup.
- [references/docs-snapshot.md](references/docs-snapshot.md): finding and saving the API's documented surface.
- [references/naming.md](references/naming.md): how a path becomes a method name, overrides, and the naming test.
- [references/testing.md](references/testing.md): recording fixtures, the offline test stack, what each test asserts.
- [references/verifier.md](references/verifier.md): running `headgate-verify`, its configuration, every rule.
