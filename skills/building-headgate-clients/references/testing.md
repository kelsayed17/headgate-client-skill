# Testing a client

A client's tests run offline, through its real headgate stack (pace, retries, breaker, error mapping), against bodies
recorded once from the live API. Nothing private is patched: the network is the `transport=` the client takes, and
time and breaker state are what `headgate.testing` sets while the client is built. Both examples' `tests/` directories
are the pattern: [lda](../../../examples/msgspec/lda/tests/) and
[Open-Meteo](../../../examples/pydantic/open_meteo/tests/).

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
