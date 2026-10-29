# Method names

A method is named in the vendor's own words where its official spec gives a usable `operationId`, and after its path
otherwise, so it can be found from the docs or the URL and checked against them. The rules and the comparison ship in
`headgate_verify.naming`; each client package runs them in its `test_method_names.py`. `headgate-verify` does not run
that test: it only checks that the file and `docs_paths.json` exist. A method named after a docs heading passes the
verifier and fails the naming test, so the naming test is part of the gate.

Each method's expected name comes from the first of these that gives one:

1. an **override** (below), reviewed in the diff with its reason;
2. the **spec**: the snapshot carries the endpoint's `operation_id` and the id passes the gate
   ([names from the spec](#names-from-the-spec));
3. the **path**, for a read ([names from the path](#names-from-the-path)). A write the spec does not name is
   unchecked.

What none of them names well is listed for review ([the review step](#the-review-step-names-no-rule-produces-well)),
where you, or the agent building the client, propose a name and record it as an override.

## Names from the spec

When `docs_paths.json` is written from an official spec (`headgate-snapshot`, see
[docs-snapshot.md](docs-snapshot.md)), each endpoint carries its `operationId`, summary and schema names, and the
method is named from them. No word list is kept: every rule reads what the endpoint itself says.

- **What the endpoint states.** A word is *stated* when the path holds it (as a word, or as a piece of four letters or
  more of a glued word: `government` in `governmententities`), or a name of the client's return models does
  (`AccountSummary` in `-> AccountSummary`). Words compare up to number with `inflect.compare` (`order` is
  `orders`). The spec's schema names count as stated for keeping a noun, but not for finding the verb, since a
  generated schema name often repeats the id's verb (`CreateOrderRequest`).
- **The verb is the first word the endpoint does not state.** `listClients` on `/clients/` is `list` + `clients`;
  `StockLatestBars` on `/stocks/bars/latest` states every word, so it has no verb.
- **A read** is `get_` and the id's words without its verb. The call-shape prefix is the caller's: a project that
  names walks `walk_` or raw bodies `fetch_` passes that prefix to `spec_name`, and the id's own read verb (`list`,
  `retrieve`, `fetch`) gives way to it.
- **A write** keeps the id's verb. When that verb only repeats the HTTP verb (`postOrder`), it takes the summary's
  first word instead ("Create an Order" gives `create_order`); a summary that starts with a stated word is a noun
  phrase, so the id's verb stays (`post_order`). An id that states every word names its verb in the path's last
  literal segment: `leaveCall` on `/calls/{id}/leave` is `leave_call`.
- **The namespace.** The leading words that 80% of each HTTP verb's ids share, in a spec of five ids or more over more
  than one verb, name the spec, not the operation, and are stripped from the ids and the summaries:
  `RetailBrokerageApi_GetAccounts` is `get_accounts`. A verb such as `get` heads only the reads, so it is never one.
- **The gate** rejects an id that is a code path (it holds a `.`: `PublicApi.TickerController.info`), the path
  written out (`get_stocks_v1_short-interest`, or FastAPI's default `<function>_<path>_<verb>`), or one that spells a
  path hole of several words, or an `{id}` hole, as words (`getOrdersOrderId` on `/orders/{order_id}`). A hole after
  a word the endpoint does not state reads as a phrase and passes (`getOrderByOrderId`).
- **The stated-word filter** drops each id word the endpoint does not state: alpaca's `GetOpenPosition` is
  `get_position`. An id that states no word gives no name.
- **Singular or plural.** A read's last noun takes the number of its path's last word when that word is the same noun
  (`getMarket` on `/markets` is `get_markets`), else is plural when the spec answers a JSON array. An object answer
  says nothing (a list usually arrives in an envelope), and inflect never singularises (it gives `censu` for
  `census`).
- **Word order.** The vendor's order stays: an id is a phrase, a path is a hierarchy.
- **Collisions.** A spec name another endpoint's name also takes keeps every id word (`getAllPositions` is
  `get_all_positions` beside `/positions/{symbol}`'s `get_positions`); one that still collides takes its path's name.

| Spec operation | Name |
|---|---|
| `GET /api/v1/clients/` `listClients` | `get_clients` |
| `GET /api/v1/constants/filing/filingtypes/` `listFilingTypes` | `get_filing_types` |
| `GET /2010-04-01/Accounts/{sid}/Applications.json` `ListApplication` | `get_applications` |
| `GET /v2/positions/{symbol}` `GetOpenPosition` | `get_position` |
| `POST /v2/watchlists` `postWatchlist`, "Create Watchlist" | `create_watchlist` |
| `DELETE /v2/orders/{order_id}` `deleteOrderByOrderID` | `delete_order` |
| `POST /2/media/upload` `mediaUpload` | `upload_media` |
| `GET /api/etfs/{ticker}/info` `PublicApi.EtfController.info` | rejected: the path names it, `get_etfs_info` |

`spec_name(endpoint, prefix=..., write=..., models=..., namespace=...)` and `spec_namespace(endpoints)` are public, so
a project with its own call shapes can name from the spec the same way.

## Names from the path

A read (a `GET`, or a method listed in `post_reads`) is named `get_` plus the literal words of its path
(`endpoint_name`):

1. Split the path on `/`. Drop empty segments, version segments (`v1`, `v2`, ..., `vX`), filler words, and path
   parameters (`{id}`). A hole inside a segment (`report-{year}.csv`) is removed and the rest kept.
2. Split each remaining segment on `-`, `_`, `.` and a lower-to-upper camelCase boundary (an all-caps run stays one
   word: `CNMSshvol`), and lower-case the words.
3. Join them with `_` after `get_`.
4. **On a collision only**, an item endpoint (its list's path plus one trailing `{param}`) whose name equals its
   list's takes its last word singular, as the `inflect` library's `singular_noun` gives it (the word itself when
   inflect finds it already singular): `GET /v1/clients/` is `get_clients` and `GET /v1/clients/{id}/` is
   `get_client`; `companies` gives `company`, `statuses` `status`, `boxes` `box`, `data` `datum`. Only that last
   word changes. A word inflect leaves as it is (`series`) still collides; a `"VERB path"` override separates it. The list endpoint must itself be a **read** (a documented `GET`, or a
   `post_reads` method's path): no collision, no singularising. So beside `POST /v2/orders` (a write, which keeps its
   verb name `create_order`), `GET /v2/orders/{id}` derives `get_orders`, and naming it `get_order` takes an
   override: `"GET /v2/orders/{id}": "get_order",  # one order; the list path is only the create endpoint`.

A path with no word (`/`, `/v1/`, `/api/v1/{id}`) derives no name: never a bare `get`, which would shadow
`AsyncBaseClient.get`. `endpoint_name` raises `ValueError` for it, and `check_names` reports such a read as needing a
`"VERB path"` override (`"GET /": "get_root",  # the API's index`) until one names it.

The default filler words are `api`, `global`, `locale`, `market`, `markets` and `us`. Examples, from the worked
examples' snapshots:

| Path | Name |
|---|---|
| `/api/v1/filings/` | `get_filings` |
| `/api/v1/filings/{filing_uuid}/` | `get_filing` |
| `/api/v1/constants/filing/filingtypes/` | `get_constants_filing_filingtypes` |
| `/v1/forecast` | `get_forecast` |
| `/v1/archive` | `get_archive` |

**Which path is named.** When the snapshot has a `source` and a method's path matches exactly one documented path,
the name comes from the **documented** path; otherwise from the client's own. A client path matches a documented path
when, with `/` stripped at both ends and every `{hole}` compared as `{}` whatever its name, it equals the documented
path or is a suffix of it on a segment boundary, with the same verb. So the docs and the client may name holes
differently, and a prefix the docs carry does not change the name. A documented path equal to the client's wins over
the suffix matches: a client `"quotes"` beside documented `/quotes` and `/v2/quotes` matches `/quotes`, and a client
`"/"` matches a documented root `GET /`, not every path.

**Writes** keep a verb name (`create_order`, `cancel_order`) and are listed in `exempt_writes`, so the path rule
skips them. A write matching exactly one documented endpoint whose spec names it is held to the spec's name; one the
spec does not name is unchecked and listed for review. An API that reads by `POST` (a search endpoint) lists those
methods in `post_reads`, and they are named like reads.

## The test file

```python
"""The client's method names follow the documented paths saved in ``docs_paths.json``."""

from pathlib import Path

from headgate_verify.naming import check_names

PACKAGE = Path(__file__).parent.parent

OVERRIDES = {
    "get_ticker_news": "get_news",  # the docs' only news endpoint; "ticker" repeats the path parameter's noun
    "GET /v2/aggs/ticker/{ticker}/prev": "get_previous_close",  # "prev" alone names nothing
}
EXEMPT_WRITES = ("create_order", "cancel_order")


def test_method_names_follow_the_docs() -> None:
    """Every documented read has one method, named after its path, and every method's path is documented."""
    problems = check_names(
        PACKAGE / "client.py",
        PACKAGE / "docs_paths.json",
        overrides=OVERRIDES,
        exempt_writes=EXEMPT_WRITES,
    )
    assert problems == []
```

Adjust `PACKAGE` to where the tests live (`Path(__file__).parent.parent` for `<package>/tests/`). `check_names`
returns one sentence per problem, so a failing assertion says what to fix. With nothing to override, it is
`assert check_names(PACKAGE / "client.py", PACKAGE / "docs_paths.json") == []`, as both examples write it.

`check_names` reads `client.py` statically and never imports it. Its keyword arguments:

| Argument | What it holds |
|---|---|
| `overrides` | the override table below |
| `exempt_writes` | write methods the naming rule skips |
| `post_reads` | methods that read by `POST`, named like reads; the project's `post-reads` when omitted |
| `filler` | the filler words; the project's `filler-words` when omitted, else the defaults above |

When `filler` or `post_reads` is not passed, `check_names` reads it from `[tool.headgate-verify]`
(`filler-words`, `post-reads`) in the `pyproject.toml` nearest the package's `client.py`, falling back to the
defaults when there is no such table; an argument passed in wins. That is the package's pyproject, while the
`headgate-verify` command reads the one nearest its working directory ([verifier.md](verifier.md#configuration)), so
in a project whose packages sit under the root's `pyproject.toml` both read the same table. No verifier rule reads
these two keys: the naming test is their reader.

## Overrides

An override is a judgement call the algorithm cannot make. Each entry maps a key to the name the method should have,
**with a one-line reason in a comment**:

- a **derived name** key (`"get_ticker_news": "get_news"`) renames every endpoint deriving that name;
- a **`"VERB path"`** key (`"GET /v2/aggs/ticker/{ticker}/prev"`) renames one endpoint. The path is compared as above
  (slashes stripped, holes as `{}`). It wins over a name key.

Use a `"VERB path"` key when two documented reads derive the same name and singularising does not separate them:
`check_names` reports the pair and the key that would separate them. An override that no longer matches any endpoint
is stale and fails the test, so the table cannot rot.

Override only for a reason a reader would accept: a name that would read wrong, or a collision. Never to keep a docs
heading's name. A spec name is overridden like a path name: by its `"VERB path"`, or by the spec name as the key.

## The review step: names no rule produces well

The check is deterministic and offline, so some names it can only take from the path, or not check at all.
`review_names` (same arguments as `check_names`) lists them, and `headgate-names` prints the list for a package:

```bash
uv run headgate-names path/to/provider/tests/test_method_names.py
```

It runs the test module's top level and reads its `PACKAGE`, and its `OVERRIDES`, `EXEMPT_WRITES`, `POST_READS` and
`FILLER` when it defines them. Listed, each with why:

- a read named by its path because the spec's `operationId` was rejected by the gate, states no word of the endpoint,
  or collided;
- a write the spec does not name, so its name is unchecked;
- a read whose path has no word;
- two methods sending one endpoint;
- a method whose path is an argument (a URL it is given), so its name is unchecked.

The list never fails the test. For each line, read the endpoint's docs. When the name it has says what the endpoint
does, leave it. When it does not, propose a name in the vendor's words and record it as a `"VERB path"` override with
a one-line reason; an endpoint an override names leaves the list. The reviewer sees each one in the diff:

```python
OVERRIDES = {
    # the spec's id is a code path; the docs title the endpoint "ETF information"
    "GET /api/etfs/{ticker}/info": "get_etf_info",
}
```

## What the test fails

- a method whose name is not the expected one (it says the expected name, and the `operationId` it came from);
- a documented `GET` with no method: the snapshot is the docs, so cover every read;
- a method whose path the snapshot does not list, or matches more than one documented path;
- two read paths that still derive one name;
- a read whose path has no word and no `"VERB path"` override;
- a stale override, or a name in `exempt_writes` / `post_reads` that is no method;
- a non-`GET` method in neither `exempt_writes` nor `post_reads`;
- a method whose path is not a string, t-string or module-level constant (or a one-level delegate to one), so it
  cannot be read;
- a `docs_paths.json` that breaks its schema ([docs-snapshot.md](docs-snapshot.md)).

When the snapshot's `source` is `null` (the API publishes no reference), the docs comparison is skipped and only the
naming rule runs.
