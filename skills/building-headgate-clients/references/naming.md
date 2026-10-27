# Method names

A read is named after its path, so the method can be found from the URL and checked against the docs. The algorithm
and the comparison ship in `headgate_verify.naming`; each client package runs them in its `test_method_names.py`.
`headgate-verify` does not run that test: it only checks that the file and `docs_paths.json` exist. A method named
after a docs heading passes the verifier and fails the naming test, so the naming test is part of the gate.

## The algorithm

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

**Writes** keep a verb name (`create_order`, `cancel_order`) and are listed in `exempt_writes`, so the naming rule
skips them. An API that reads by `POST` (a search endpoint) lists those methods in `post_reads`, and they are named
like reads.

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
heading's name.

## What the test fails

- a method whose name is not the expected one (it says the expected name);
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
