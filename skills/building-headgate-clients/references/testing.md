# Testing a client

A client's tests run offline, through its real headgate stack (pace, retries, breaker, error mapping), against bodies
recorded once from the live API. Nothing private is patched: the network is the `transport=` the client takes, and
time and breaker state are what `headgate.testing` sets while the client is built. Both examples' `tests/` directories
are the pattern: [lda](../../../examples/msgspec/lda/tests/) and
[Open-Meteo](../../../examples/pydantic/open_meteo/tests/).

## The shared helpers (`headgate_verify.testing`)

Any client tests the same way with the helpers `headgate-verify` ships, in the dev group as
`headgate-verify[testing]` (or `[recording]`, which adds vcrpy and pytest-recording). Each is a module imported by
name:

| Module | What it gives a client's suite |
|---|---|
| `manifest` | `Endpoint(method=, path=, envelope=, ...)`, the one table the client tests, the recording and the fidelity walk read; `manifest_drift(Client, MANIFEST)` names each endpoint with no entry and each entry naming no method |
| `fidelity` | `findings(pairs)` over `(body, decode target)` pairs: wire keys no struct declares, declared fields no body fills; `assert_matches_baseline(found, load_baseline(tests_dir))` against `_fidelity_baseline.toml` |
| `recording` | `Recording(placeholders=..., redact_keys=..., scrub_body=...)`, whose `vcr_config()` scrubs every credential handed out, every token, every header but `Content-Type`; the `replay_credentials` and `no_retry_backoff` fixtures; `drive(client, endpoint)` and `recorded(MANIFEST)` |
| `cassettes` | the bodies a cassette recorded, per endpoint path (`endpoint_bodies`, `recorded_bodies`) |
| `creds` + `plugin` | credentials by `(provider, field)` from the operator's `--credentials-provider module:function`; a missing one skips |
| `leaf_mock` | `install(client, MockHTTP())` for a client that takes no `transport=` (a curl leaf) |

The msgspec example's [test_fidelity.py](../../../examples/msgspec/lda/tests/test_fidelity.py) is the pattern for
the first two:

```python
MANIFEST = [Endpoint(method="get_filing", path="/filings/{filing_uuid}/", envelope=Filing, fixture="filing.json"), ...]


def test_the_manifest_lists_every_endpoint() -> None:
    if report := manifest_drift(LdaClient, MANIFEST):
        pytest.fail(report)  # not `assert`: pytest elides the middle of a long message


def test_every_recorded_body_matches_the_structs_and_the_baseline() -> None:
    pairs = [(json.loads((FIXTURES / e.fixture_name).read_bytes()), e.envelope) for e in MANIFEST]
    assert_matches_baseline(findings(pairs), load_baseline(Path(__file__).parent))
```

- **`envelope` is the reader's decode target**, not the method's return type: `decoder(Page[Filing])` is walked as
  `Page[Filing]`, so the envelope's own keys are checked too.
- **A walk is an endpoint** (`paginated=True`; a recording reads its first page). When every walk sits beside a
  single-page method on the same path, pass `include_walks=False` and list the page method.
- **`capture=False`** keeps an endpoint that writes (an order, a delete) in the table for the exhaustiveness check
  while a recording never calls it; **`strict=False`** mirrors a reader that decodes leniently.
- **The baseline is exact.** Each entry is `"Struct.name" = { reason = "...", date = "YYYY-MM-DD", kind = "..." }`,
  `kind` one of `deliberate`, `fixture-gap`, `entitlement`, `source-defect` (an undeclared key is only `deliberate` or
  `source-defect`: the wire did send it). A new finding fails as drift and an entry nothing shows fails as stale.
- **msgspec only.** The walk reads msgspec struct fields; a pydantic client has no fidelity check yet.

## Recording with cassettes

A client with credentials, or more endpoints than a hand-recorded fixture per read can keep up with, records vcrpy
cassettes instead: one recorded test drives every manifest entry through the client's real stack, and the same test
replays offline. vcrpy patches httpx2's own transports, below headgate's stack, so the client is built with no
`transport=`. A client on a curl leaf is not recorded this way.

```python
# tests/conftest.py
pytest_plugins = ["headgate_verify.testing.plugin"]  # --credentials-provider module:function

# tests/<package>/conftest.py
RECORDING = Recording(placeholders={("lda", "api_key"): "replay-lda-api-key"})


@pytest.fixture(scope="module")
def vcr_config() -> dict[str, object]:
    return RECORDING.vcr_config()


@pytest.fixture
def recording() -> Recording:
    return RECORDING


# tests/<package>/test_recorded.py
from headgate_verify.testing.recording import drive, no_retry_backoff, recorded, replay_credentials  # noqa: F401


@pytest.mark.vcr
@pytest.mark.parametrize("endpoint", recorded(MANIFEST))
async def test_endpoint(endpoint: Endpoint) -> None:
    key = require("lda", "api_key")["api_key"]
    await drive(LdaClient(api_key=key, user_agent=USER_AGENT), endpoint)
```

- **Record** with `pytest tests/<package>/test_recorded.py --record-mode=rewrite --credentials-provider ops:lookup`;
  every other run replays, and a request the cassette lacks fails. Read every cassette before committing it.
- **Only what was handed out is scrubbed**, in every spelling (raw, percent-encoded, base64, JSON-escaped), plus each
  replay placeholder and each value under a `redact_keys` JSON key (minted tokens by default). Add the keys a
  provider echoes (an account number) to `redact_keys`, and anything else private through `scrub_body`. Never scrub
  by guessing: a redacted cursor cannot be told from a real one.
- **headgate's `CassetteFilter`** composes: `Recording(cassette_filter=CassetteFilter(auths=(auth,)))`, with the
  filter in the client's middleware, keeps token mints out of the cassette.
- **The fidelity walk reads the cassettes**: `recorded_bodies(CASSETTES / "test_recorded", endpoint)` gives the bodies
  `test_endpoint[<method>].yaml` holds for the endpoint's path.

The worked examples' fixtures predate the cassettes and are hand-recorded JSON; the rules below hold for both.

## Recording fixtures

- **Read the terms first** and stay inside them: send the self-identifying User-Agent you will build the client with,
  pace requests well under the documented limit, and count every request (docs pages included) for the module
  docstring.
- **Record one body per documented read**, and one per documented error you can provoke within the terms: a bad
  parameter (`400`), an unknown id (`404`), an empty result. Save each as sent under `fixtures/<name>.json`, named
  after the method (`filing.json`, `filings_empty.json`, `filings_bad_year.json`).
- **Trim lists** to a couple of rows (and `page_size=2` on the request) so a fixture stays readable; keep every field.
- **Redact personal data**: a private person's name, telephone, e-mail, or a residential street address and ZIP becomes
  `"REDACTED"`. Keep what the API is about (a company, a registrant, a public official in that role); when unsure,
  redact. Say in the test module's docstring what was redacted.
- **A body you could not record** (provoking a `429` would break the terms, a `401` needs a bad key) is built in the
  test from the docs' own example, with a comment naming where it came from.

## The fixtures (`conftest.py`)

```python
@pytest.fixture
def fake() -> FakeTransport:
    return FakeTransport()  # each test adds the routes it serves


@pytest.fixture
def clock() -> TestClock:
    return TestClock()  # moves only when the client sleeps on it


@pytest.fixture
async def lda(fake: FakeTransport, clock: TestClock) -> AsyncIterator[LdaClient]:
    with clock.install(), isolated_breakers():
        async with LdaClient(user_agent=USER_AGENT, transport=fake) as client:
            yield client
```

- **Build the client inside the context managers.** headgate reads the clock and the breaker registry when a client
  is constructed; entering them around an existing client changes nothing.
- **A paced client is built under `TestClock().install()`.** Each wait for its turn then advances the test clock
  instead of taking time, so the pace holds and can be asserted (`clock.now == pytest.approx(10.0)` after two calls at
  one every 10 seconds) while the test takes no time. Retries wait on it too.
- **`instant_retries()` is for an unpaced client** (or a test of the retry sequence alone). It keeps the real clock
  and makes every wait return at once, so a paced client's queue still measures wall time and a long walk can pass its
  deadline.
- **`isolated_breakers()` always**, so a failure in one test opens no breaker in the next.
- **A shared `RateBudget`** is built in the test with the clock's timing, `RateBudget(PACE, max_in_flight=...,
  timing=clock.timing)`, and given to every client that shares it: a budget measures time on the timing it was built
  with, not on an installed clock.
- Tests run under anyio: `pytestmark = pytest.mark.anyio`, with `anyio` and `pytest` in the dev group.

## Snapshots

Each decode test asserts `decoded == snapshot` with syrupy's JSON extension, so a snapshot file reads like the wire.
Serialize a decoded value with the flavour's `to_builtins` first:

```python
class StructSnapshot(JSONSnapshotExtension):
    @override
    def serialize(self, data, *, exclude=None, include=None, matcher=None):
        return super().serialize(msgspec.to_builtins(data), exclude=exclude, include=include, matcher=matcher)


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    return snapshot.use_extension(StructSnapshot)
```

The pydantic example uses `headgate.pydantic.to_builtins`. Write snapshots with `pytest --snapshot-update`, then read
every one before committing: a snapshot is a claim about what the API sent.

## What the tests cover

- **Every documented read decodes** its recorded body to the snapshot, from exactly one request to exactly the
  documented URL. A table of cases (fixture, call, expected URL) parametrizes one test:

  ```python
  fake.reply("GET", urlsplit(case.url).path, recorded(f"{case.fixture}.json"))
  decoded = await case.read(lda)
  assert [str(request.url) for request in fake.calls] == [case.url]
  assert decoded == snapshot
  ```

  A `FakeTransport` route matches the method and the path exactly as sent (with the base path, percent-encoded as a
  t-string escapes it), never the host or the query. So assert the full URL, host and query included, from
  `fake.calls`.
- **The request side**: the User-Agent starts with the caller's product (`USER_AGENT + " headgate/"`), fixed headers
  (`Accept`) are sent, credentials go where the auth puts them, and query parameters arrive as the docs spell them.
- **Each documented error** raises its headgate type, served the recorded body with its status: a bad parameter is
  `UpstreamStatusError` with the API's reason in the message, a throttle is `RateLimitError` with `retry_after`, a
  bad credential `AuthError`. Assert how many requests were sent (a `400` is not retried).
- **Each documented answer** returns what the method declares (an unknown id is `None`).
- **The pace**: two back-to-back calls advance the test clock by one interval. With a shared budget, a call on one
  host waits for the other's.
- **A walk**: it sends the caller's query first, then the URL each page names, and stops where the API says; an empty
  result is an empty walk after one request; a walk that keeps going raises `PageLimitError` after exactly
  `MAX_PAGES` requests.
- **The names**: `test_method_names.py` ([naming.md](naming.md)).

Run them with `uv run pytest <tests dir>`. They must pass with no network: a request with no route raises
`UnmatchedRequestError`, so a test that reaches past the fake fails instead of calling the API.
