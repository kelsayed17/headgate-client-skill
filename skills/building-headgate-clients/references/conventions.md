# The conventions

What a headgate client looks like when it is done. The two worked examples keep every rule here:
[examples/msgspec/lda/](../../../examples/msgspec/lda/) and [examples/pydantic/open_meteo/](../../../examples/pydantic/open_meteo/).
Copy their shape; read headgate's own `examples/` only to learn headgate's API, since each of them breaks at least one
rule below (`github_client.py`, `orders_client.py`, `series_client.py` and `quickstart.py` all do).

Each rule names the verifier rule that checks it, where one does; [verifier.md](verifier.md) lists them all.

## Project setup

- Python 3.14 or later, and headgate 0.7.0 or later with the extra of your flavour, in the project's own
  `pyproject.toml` (the one nearest the package). `one-flavour` checks it:

  ```toml
  [project]
  requires-python = ">=3.14"
  dependencies = ["headgate[msgspec]>=0.7.0"]     # or headgate[pydantic]

  [dependency-groups]
  dev = ["headgate-verify", "pytest", "anyio", "syrupy"]
  ```

  The extra may sit in `[project].dependencies`, any list of `[project.optional-dependencies]` or any list of
  `[dependency-groups]`; any `headgate[...]` whose extras include the flavour's counts. headgate's network layer is
  httpx2; never import `httpx`.
- **Tell ruff the models are read at run time.** msgspec and pydantic read a model's annotations when it is defined.
  ruff's flake8-type-checking rules would otherwise move a field type's import (`datetime`, `Decimal`, `UUID`, another
  module's model) under `if TYPE_CHECKING:`, and the model then fails at import. The examples rely on this setting:

  ```toml
  [tool.ruff.lint.flake8-type-checking]
  runtime-evaluated-base-classes = ["msgspec.Struct", "pydantic.BaseModel"]
  ```

- Project lists the verifier reads go in `[tool.headgate-verify]` (see [verifier.md](verifier.md#configuration)), and
  `headgate-verify` reads it from the `pyproject.toml` nearest the working directory, so run it from the project
  root; the naming test's `check_names` reads `filler-words` and `post-reads` from the one nearest the package.

## The package

```
<provider>/
  __init__.py           a docstring only: no imports, no re-exports, no __all__
  client.py             one AsyncBaseClient subclass per host
  models.py             wire models, and a <Endpoint>Params TypedDict per endpoint's query
  pagination.py         pagers and page budgets, if the API pages; never a page loop
  docs_paths.json       the docs snapshot
  tests/                (or tests/<provider>/ beside the package, or under the project root)
    test_client.py      offline tests through the real headgate stack
    test_method_names.py  the naming test
    fixtures/           bodies recorded from the live API
    __snapshots__/      syrupy snapshots of the decoded values
```

`package-layout` checks the files, `model-has-no-provider-prefix` the model names. One provider with several hosts
keeps them in one package, one class per host (the Open-Meteo example).

## The client class

- **Subclass `AsyncBaseClient` directly**, with no other base and no decorator. One `super().__init__(...)` call, with
  keyword arguments and no `*`/`**` splat (`client-constructor`, `client-method-shape`, `one-class-per-host`).
- **`base_url=` is a module-level name** bound to a string: `BASE_URL = "https://lda.gov"`. Never a literal in the
  call, a parameter or an expression (`client-base-url`, `one-class-per-host`). Two classes never name the same host.
- **The base URL is a host with no path** (`client-base-url-has-no-path`). Every method's path spells the API's prefix
  out: `"api/v1/filings/"`, `t"api/v1/filings/{filing_uuid}/"`. A prefix cannot be a constant joined to the path (that
  is a built path, which the `client-paths-*` rules refuse), and it cannot ride a t-string hole (headgate escapes a
  hole as one segment, so its `/` would be sent as `%2F`).
- **`rate=` always.** headgate's default is unlimited, so a client states its pace: `PACE = Rate.per_second(0.1)` for
  one request every 10 seconds. Pace below the documented limit so the server never has to slow you down
  (`client-constructor`).
- **One budget for one quota.** When the provider counts one quota across several hosts or clients (per IP address,
  per key), build one `RateBudget(PACE, max_in_flight=...)` and pass the same object as `rate=` to every client that
  spends from it, taken as a constructor argument. A module-level factory builds the production budget
  (`free_api_budget()` in the Open-Meteo example); a test builds it on its clock. Two budgets for one quota let
  pushback from one host leave the other at full speed.
- **The User-Agent is a constructor argument with no default**, passed as `HttpOptions(user_agent=user_agent)`.
  headgate sends it first, before its own product tokens. Never a literal in the package, and never a `"User-Agent"`
  key in `headers=` (`client-user-agent-has-no-default`, `client-no-identity-user-agent`). A host that refuses
  anything but a browser User-Agent is the one exception: list its package in `browser-user-agent-packages`
  (`client-browser-user-agent-only-where-allowed`).
- **Accept `transport=` and pass it through** as `HttpOptions(transport=transport)`, typed
  `httpx2.AsyncBaseTransport | None = None`. It is the seam the tests use (`client-accepts-transport`).
- **Credentials are constructor arguments**, set once through headgate's auth classes (`BearerAuth`,
  `StaticHeaderAuth`, `QueryParamAuth`, `CachedTokenAuth`) as `auth=`. Never in `HttpOptions(headers=)`
  (`client-default-headers-carry-no-credential`), and never read from the environment or a `.env` file
  (`client-reads-no-environment`): the code that builds the client owns its configuration.
- Fixed request headers the API needs (`{"Accept": "application/json"}`) go in `HttpOptions(headers=...)`.
- A transport you need to change is **subclassed**, calling `super().handle_async_request`, never wrapped around
  another transport (`client-transport-subclassed-not-wrapped`). A curl-impersonating transport passes
  `default_headers=True` and names no User-Agent of its own (`client-impersonating-transport-owns-its-headers`,
  `client-no-user-agent-beside-impersonation`).

## Module-level values

Everything a method passes besides its own arguments is built once, at import, at module level, so a bad declaration
fails when the module loads, not on the first call:

```python
FILINGS = decoder(Page[Filing])  # a reader
FILING = decoder(Filing)
FILING_OR_NONE = Expect(FILING).on(HTTPStatus.NOT_FOUND, nothing)  # a documented answer
NEW_ORDER = encoder(NewOrderBody)  # a writer
ORDER_RETRY = RetryPolicy(attempts=1)  # a non-idempotent write's retry policy
```

Pagers and page budgets live in `pagination.py` (below). In a method, `expect=`, `pages=` and `limit=` are bare
UPPER_CASE names the module binds; a call there (`expect=decoder(Filing)`, `expect=Expect(...)`) is reported by
`client-method-shape`. headgate's own `nothing` and `as_bytes` may be passed to `expect=` by name. `retry=` and
`deadline=` take such a name, a literal or a parameter of the method; `timeout=` takes such a name or a parameter
(headgate takes a `Timeouts`, so one built at the call is a module constant instead). Path constants are module-level too, never class attributes (`client-path-constants-at-module-level`); a name
ending `_URL` holds an absolute URL, a relative one ends `_PATH` (`client-url-suffix-means-absolute`).

## Endpoint methods

- **One public method per documented endpoint**, named after its path ([naming.md](naming.md)). Cover every documented
  read: the naming test fails a documented `GET` with no method.
- **The body is one statement** after an optional docstring (`client-method-shape`):

  ```python
  async def get_filing(self, filing_uuid: str) -> Filing | None:
      """Return the filing ``filing_uuid``, or ``None`` when there is none."""
      return await self.get(t"api/v1/filings/{filing_uuid}/", expect=FILING_OR_NONE)


  async def get_forecast(self, **params: Unpack[ForecastParams]) -> Forecast:
      """Return the forecast at ``params``' location."""
      return await self.get("v1/forecast", params=params, expect=FORECAST)
  ```

  A write that returns nothing is annotated `-> None` and passes headgate's `nothing` reader:
  `await self.delete(t"v2/watchlists/{watchlist_id}", expect=nothing)` (every verb but `head()` needs `expect=`, and
  `client-method-returns` asks a `-> None` method for `expect=nothing`). A write's body goes through a module-level
  writer: `return await self.post("v2/orders", body=NEW_ORDER(order), expect=ORDER, retry=ORDER_RETRY)`.
- **Path parameters are positional arguments** interpolated into a t-string. Query parameters arrive as
  `**params: Unpack[<Endpoint>Params]` and are forwarded as `params=params`; never a `params` mapping argument.
  The collector reaches the wire untouched, in every module and through every leg: not rebound or mutated, not
  merged with a constant, no keyword handed beside it to a leg whose own collector would catch it, and no `?` query
  written into the path (`client-query-params-are-a-typeddict`).
- **A path with holes is a t-string**; a path with none is a plain string literal. Never an f-string, `.format()`, a
  hand-built `Template`, `quote()` on a hole, string concatenation, or a variable holding a built path
  (`client-paths-no-f-string`, `client-paths-no-format-on-path-name`, `client-paths-no-template-construction`,
  `client-path-holes-are-escaped-once`, `client-paths-no-built-sink-argument`). `{value:raw}` is headgate's escape
  hatch for a pre-built fragment; its format spec is a literal (`client-paths-no-dynamic-format-spec`).
- **A class calls only its own host.** A URL the API itself returns (a `next` link in a body) may be followed, as a
  pager does; an absolute URL literal or constant naming another host is reported (`one-class-per-host`).
- **The return annotation names the decoded type**: `Filing`, `list[Constant]`, `Filing | None`. Never
  `httpx2.Response`, `dict` or `Any` (`client-method-returns`).
- **A non-idempotent write names its retry policy** with `retry=`, a module-level `RetryPolicy` or a literal: a
  re-sent order is a second order. A method whose name holds one of `write-name-fragments` is such a write unless it
  is a `cancel_`/`preview_` (`client-order-writes-name-retry`).
- A method that cannot be one statement (a streamed download is an `async with self.stream(...)` block) carries an
  allow comment on its `def` line with the reason: `# headgate-verify: allow client-method-shape -- <reason>`.

## Documented answers

A documented non-2xx response that means something ("no such filing") is declared at module level, next to the reader
it extends, and the method returns `<Type> | None`:

```python
FILING_OR_NONE = Expect(FILING).on(HTTPStatus.NOT_FOUND, nothing)  # an unknown uuid
```

The status is an `int` literal or an `HTTPStatus` member, never computed (`client-answer-status-is-literal`). Declare
only what the API documents or you measured; every other status raises a headgate error (`UpstreamStatusError`,
`RateLimitError`, `AuthError`, ...), which is the caller's to handle.

## Pagination

A paged list is a plain (sync) `def` whose one statement returns headgate's lazy walk:

```python
def get_filings(self, **params: Unpack[FilingsParams]) -> Paginated[Page[Filing], Filing]:
    """Walk the filings that match ``params``, page by page as iterated."""
    return self.paginate("api/v1/filings/", params=params, expect=FILINGS, pages=FILING_PAGES, limit=PAGE_LIMIT)
```

- `pages=` is a pager matching the API's own paging (`NextUrl` over a body's `next` URL, `Cursor`, `Offset`,
  `LinkHeader`, `Next`), and `limit=` a `PageLimit(MAX_PAGES)` budget; both are required, both module-level names
  from `pagination.py`. A walk without a page budget is unbounded. With headgate's default `on_limit="raise"`, a walk
  that hits the budget raises `PageLimitError`, so a caller never mistakes a cut-short walk for the whole result.
- `pagination.py` holds the pagers, the budget and any helper that reads a page (`items=`, `next=`), never a page loop
  (`client-no-hand-rolled-page-loop`). Its docstring says how the API pages and why the budget is what it is (pages
  times the pace is a duration: say it).

## Models

- **msgspec:** `class Filing(msgspec.Struct, frozen=True, gc=False)`, fields only: no methods, properties or computed
  members (`client-wire-structs-are-data`). `frozen=True, gc=False` come first in the keywords: a decoded body is a
  tree, so no instance sits in a reference cycle and the garbage collector need not track it. A subclass of a struct
  inherits both and never overrides either (`client-wire-structs-are-frozen-without-gc`). Decoded with
  `headgate.msgspec.decoder`.
- **pydantic:** a `BaseModel` with `model_config = ConfigDict(frozen=True)`, fields only: no methods, properties or
  validators (`client-pydantic-models-are-data`). Decoded with `headgate.pydantic.decoder` (strict by default).
- **Field names are the API's own**; msgspec's `rename=` or a pydantic alias where Python cannot spell one. Types say
  what the wire sends: `UUID`, `date`, `datetime`, `Decimal` for money sent as a string, `X | None` only where the wire
  sends `null` (the spec is often wrong about nullability: trust the recorded bodies, and say in the docstring where
  the two disagree). A field the API always sends has no default, so a body that drops it fails to decode.
- **No provider prefix** on any class in `models.py` (`model-has-no-provider-prefix`). Query params are
  `<Endpoint>Params` (`TypedDict`, `total=False`, `Required[...]` for a required one); a request body is
  `<Endpoint>Body`.
- Import what you use by name: `from headgate.msgspec import decoder`, never `import headgate.msgspec` or
  `from headgate import msgspec` (`client-serde-imported-by-name`). One flavour per package (`one-flavour`).
- A block whose keys the request chooses (Open-Meteo's `hourly`) is a typed map, not a model; its docstring says why.

## Errors

A method returns its decoded type or raises a headgate error. No `try`/`except` in a client module; the one exception
re-raises as a more specific headgate error. Every `except` is reported as a warning (`client-except-needs-review`)
for a reader to confirm, with an allow comment carrying the reason. A multi-type `except` names a module-level tuple
constant (`except _UNREADABLE:`), never a tuple written in the clause: at Python 3.14 `ruff format` rewrites
`except (A, B):` as `except A, B:`, which reads as Python 2 (`client-except-names-a-tuple-constant`).

## Caching

headgate caches through `TransportPolicy(cache=HttpCache(...))`. Its default partition, `Partition.CREDENTIAL`, keys
every entry by the credential and never stores `Authorization`, so a cached bearer client is safe as it is.
`Partition.SHARED` serves one credential's responses to another: use it for public data only. A class that builds a
bearer auth and a cache whose partition is `SHARED`, or one the verifier cannot read, is warned about
(`client-cache-with-bearer-auth`).

## Strings

String literals spell every character as itself, with no hex, unicode, named or octal escape (`\x`, `\u`, `\U`, `\N`)
(`client-strings-carry-no-encoded-characters`), and no placeholder contact such as an `example.com` address
anywhere in the package (`client-no-placeholder-contact`).

## The module docstring

`client.py`'s docstring is the client's record of the API. It says:

- what the API is, its base URL, whether it needs a key, and which class serves which host;
- **the terms**: the URL, when you read it, the limits and attribution it asks for, and what this client does about
  each (it returns values as sent; attribution is the caller's);
- **the pace** and why it is what it is: the documented limit, the margin, what a `429` does under headgate's retry
  policy;
- **what was measured**, with the date, the request count and the User-Agent sent: the status and content type of each
  read, an empty result, each error body (bad parameter, not found, bad credential, throttle), any quirk (an `Accept`
  the server insists on);
- **what was not measured** (a `429` you could not provoke within the terms, a `401` with no key), so nobody mistakes
  a documented shape for a recorded one.

`models.py` and `pagination.py` say where the spec and the wire disagree and why a budget is what it is. The verifier
does not read docstrings; the reviewer does.
