# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Tests for the method-name helper: the path-to-name algorithm, the docs snapshot, the endpoint reader, the check.

The ``endpoint_name`` values are the measured renames of the project this algorithm came from, and are the spec.
"""

import json
from datetime import date
from typing import TYPE_CHECKING

import pytest

from headgate_verify.endpoints import client_endpoints
from headgate_verify.naming import DEFAULT_FILLER, check_names, endpoint_name
from headgate_verify.snapshot import DocsSnapshot, Endpoint, SnapshotError, load_snapshot

if TYPE_CHECKING:
    from pathlib import Path

_SOURCE = "https://api.example/openapi.json"


def _client(tmp_path: Path, body: str, *, header: str = "") -> Path:
    path = tmp_path / "client.py"
    path.write_text(f"{header}\n\nclass Client(AsyncBaseClient):\n{body}", encoding="utf-8")
    return path


def _snapshot(
    tmp_path: Path, endpoints: list[tuple[str, str]], *, source: str | None = _SOURCE, reason: str | None = None
) -> Path:
    path = tmp_path / "docs_paths.json"
    data = {
        "source": source,
        "retrieved": "2026-10-26",
        "reason": reason,
        "endpoints": [{"verb": verb, "path": route} for verb, route in sorted(endpoints, key=lambda e: (e[1], e[0]))],
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _get(name: str, route: str) -> str:
    return f"    async def {name}(self) -> X:\n        return await self.get({route}, expect=X)\n\n"


# endpoint_name


def test_endpoint_name_keeps_a_leading_literal_and_drops_the_version() -> None:
    """``/benzinga/v1/analyst-insights`` is ``get_benzinga_analyst_insights``."""
    assert endpoint_name("/benzinga/v1/analyst-insights") == "get_benzinga_analyst_insights"


def test_endpoint_name_drops_a_trailing_parameter() -> None:
    """``/v3/reference/tickers/{ticker}`` is ``get_reference_tickers``; a collision is ``check_names``'s business."""
    assert endpoint_name("/v3/reference/tickers/{ticker}") == "get_reference_tickers"


def test_endpoint_name_splits_camel_case_and_drops_filler() -> None:
    """``quoteSummary`` splits into ``quote_summary``; ``finance`` is filler here."""
    assert endpoint_name("/v1/finance/quoteSummary/{symbol}", filler=DEFAULT_FILLER | {"finance"}) == (
        "get_quote_summary"
    )


def test_endpoint_name_drops_an_inner_parameter() -> None:
    """``/v2/stocks/{symbol}/bars`` is ``get_stocks_bars``."""
    assert endpoint_name("/v2/stocks/{symbol}/bars") == "get_stocks_bars"


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/CNMSshvol", "get_cnmsshvol"),
        ("/vX/things", "get_things"),
        ("/v10/a_b.c-d", "get_a_b_c_d"),
        ("/api/markets/quotes", "get_quotes"),
        ("view.xml", "get_view_xml"),
        ("/v1beta/x", "get_v1beta_x"),
    ],
)
def test_endpoint_name_cases(path: str, expected: str) -> None:
    """No split inside an all-caps run; ``vX`` is a version; ``_``, ``.`` and ``-`` split; default filler drops."""
    assert endpoint_name(path) == expected


def test_endpoint_name_prefix() -> None:
    """The prefix is a parameter."""
    assert endpoint_name("/v1/orders", prefix="list_") == "list_orders"


@pytest.mark.parametrize("path", ["/", "/v1/", "/api/v1/{id}", ""])
def test_endpoint_name_refuses_a_path_with_no_word(path: str) -> None:
    """A path with no literal word derives no name: never ``get``, which would shadow ``AsyncBaseClient.get``."""
    with pytest.raises(ValueError, match="no word"):
        endpoint_name(path)


# load_snapshot


def test_load_snapshot(tmp_path: Path) -> None:
    """A valid snapshot loads into its dataclass."""
    path = _snapshot(tmp_path, [("GET", "/v1/foo/{id}"), ("POST", "/v1/foo")])
    assert load_snapshot(path) == DocsSnapshot(
        _SOURCE, date(2026, 10, 26), None, (Endpoint("POST", "/v1/foo"), Endpoint("GET", "/v1/foo/{id}"))
    )


@pytest.mark.parametrize(
    ("data", "fragment"),
    [
        ([], "must be a JSON object"),
        ({"source": None, "retrieved": "2026-10-26", "reason": None, "endpoints": []}, "reason"),
        ({"source": _SOURCE, "retrieved": "26/10/2026", "reason": None, "endpoints": []}, "YYYY-MM-DD"),
        ({"source": _SOURCE, "retrieved": "2026-10-26", "endpoints": []}, "reason"),
        ({"source": _SOURCE, "retrieved": "2026-10-26", "reason": None, "endpoints": [], "x": 1}, "unknown key"),
        ({"source": _SOURCE, "retrieved": "2026-10-26", "reason": None, "endpoints": {}}, "endpoints"),
        (
            {"source": _SOURCE, "retrieved": "2026-10-26", "reason": None, "endpoints": [{"verb": "get", "path": "/"}]},
            "upper-case",
        ),
        (
            {
                "source": _SOURCE,
                "retrieved": "2026-10-26",
                "reason": None,
                "endpoints": [{"verb": "GET", "path": "/b"}, {"verb": "GET", "path": "/a"}],
            },
            "sorted",
        ),
        (
            {
                "source": _SOURCE,
                "retrieved": "2026-10-26",
                "reason": None,
                "endpoints": [{"verb": "GET", "path": "/a"}, {"verb": "GET", "path": "/a"}],
            },
            "twice",
        ),
    ],
)
def test_load_snapshot_rejects(tmp_path: Path, data: object, fragment: str) -> None:
    """Each schema violation is a ``SnapshotError`` naming what is wrong."""
    path = tmp_path / "docs_paths.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(SnapshotError, match=fragment):
        load_snapshot(path)


def test_load_snapshot_rejects_invalid_json(tmp_path: Path) -> None:
    """Text that is not JSON is a ``SnapshotError``."""
    path = tmp_path / "docs_paths.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(SnapshotError, match="not valid JSON"):
        load_snapshot(path)


# client_endpoints


def test_client_endpoints_reads_each_form(tmp_path: Path) -> None:
    """Strings, t-strings, module constants, paginate, stream and one-level delegation are read; a parameter is not."""
    header = (
        '_PATH = "v1/things"\n_BASE = "v2"\n\nasync def _leg(client, path, x):\n    return await client.get(path)\n'
    )
    body = (
        _get("get_a", '"v1/a"')
        + _get("get_b", 't"{_BASE}/b/{item_id!r}/{self.account}"')
        + _get("get_things", "_PATH")
        + '    def get_pages(self) -> P:\n        return self.paginate(t"v1/pages/{x}", expect=X, pages=Y)\n\n'
        + "    def open_feed(self) -> S:\n        return self.stream('feed', method=\"POST\")\n\n"
        + '    async def create_c(self, body: B) -> C:\n        return await self.post("v1/c", body=body, expect=X)\n\n'
        + '    async def get_d(self) -> D:\n        return await self._d("v1/d", 3)\n\n'
        + "    async def _d(self, path: str, n: int) -> D:\n        return await self.get(path, expect=X)\n\n"
        + '    async def get_e(self) -> E:\n        return await _leg(self, x=1, path="v1/e")\n\n'
        + "    async def get_f(self, url: str) -> F:\n        return await self.get(url, expect=X)\n\n"
        + "    async def get_g(self) -> G:\n        return await self._g(1)\n\n"
        + '    async def _g(self, n: int) -> G:\n        return await self.get(t"v1/g/{n}", expect=X)\n\n'
        + "    @property\n    def name(self) -> str:\n        return 'x'\n"
    )
    assert client_endpoints(_client(tmp_path, body, header=header)) == {
        "get_a": Endpoint("GET", "v1/a"),
        "get_b": Endpoint("GET", "v2/b/{item_id}/{self.account}"),
        "get_things": Endpoint("GET", "v1/things"),
        "get_pages": Endpoint("GET", "v1/pages/{x}"),
        "open_feed": Endpoint("POST", "feed"),
        "create_c": Endpoint("POST", "v1/c"),
        "get_d": Endpoint("GET", "v1/d"),
        "get_e": Endpoint("GET", "v1/e"),
        "get_g": Endpoint("GET", "v1/g/{n}"),
    }


# check_names


def test_matching_client(tmp_path: Path) -> None:
    """A client whose names follow its documented reads has no problems."""
    client = _client(tmp_path, _get("get_stocks_bars", 't"v2/stocks/{symbol}/bars"'))
    assert check_names(client, _snapshot(tmp_path, [("GET", "/v2/stocks/{symbol}/bars")])) == []


def test_collision_singularises_item_endpoint(tmp_path: Path) -> None:
    """``/v3/reference/tickers`` and ``.../{ticker}`` are ``get_reference_tickers`` and ``get_reference_ticker``."""
    body = _get("get_reference_tickers", '"v3/reference/tickers"') + _get(
        "get_reference_ticker", 't"v3/reference/tickers/{ticker}"'
    )
    snapshot = _snapshot(tmp_path, [("GET", "/v3/reference/tickers"), ("GET", "/v3/reference/tickers/{ticker}")])
    assert check_names(_client(tmp_path, body), snapshot) == []


def test_collision_misnamed_item_endpoint_reported(tmp_path: Path) -> None:
    """With the collision, the plural name on the item endpoint is reported."""
    body = _get("get_reference_tickers_list", '"v3/reference/tickers"') + _get(
        "get_reference_tickers", 't"v3/reference/tickers/{ticker}"'
    )
    snapshot = _snapshot(tmp_path, [("GET", "/v3/reference/tickers"), ("GET", "/v3/reference/tickers/{ticker}")])
    problems = check_names(_client(tmp_path, body), snapshot)
    assert any("get_reference_tickers" in p and "should be named get_reference_ticker" in p for p in problems), problems


@pytest.mark.parametrize(
    ("plural", "singular"),
    [
        ("companies", "company"),
        ("addresses", "address"),
        ("categories", "category"),
        ("statuses", "status"),
        ("boxes", "box"),
        ("tickers", "ticker"),
        ("orders", "order"),
        ("data", "datum"),
    ],
)
def test_item_endpoint_singularises_with_inflect(plural: str, singular: str, tmp_path: Path) -> None:
    """The item endpoint's last word is the English singular of its list's, not the plural minus one ``s``."""
    body = _get(f"get_{plural}", f'"v1/{plural}"') + _get(f"get_{singular}", f't"v1/{plural}/{{key}}"')
    snapshot = _snapshot(tmp_path, [("GET", f"/v1/{plural}"), ("GET", f"/v1/{plural}/{{key}}")])
    assert check_names(_client(tmp_path, body), snapshot) == []


def test_only_the_last_word_singularises(tmp_path: Path) -> None:
    """``/v1/news-statuses/{id}`` beside its list is ``get_news_status``: only the last literal word changes."""
    body = _get("get_news_statuses", '"v1/news-statuses"') + _get("get_news_status", 't"v1/news-statuses/{key}"')
    snapshot = _snapshot(tmp_path, [("GET", "/v1/news-statuses"), ("GET", "/v1/news-statuses/{key}")])
    assert check_names(_client(tmp_path, body), snapshot) == []


def test_wordless_read_needs_a_path_override(tmp_path: Path) -> None:
    """A documented read whose path derives no word is reported as needing a ``"VERB path"`` override."""
    client = _client(tmp_path, _get("get_root", '"/"'))
    problems = check_names(client, _snapshot(tmp_path, [("GET", "/")]))
    assert len(problems) == 1, problems
    assert problems[0] == 'the read GET / derives no name from its path; add an override keyed "GET /"'


def test_wordless_read_takes_its_path_override(tmp_path: Path) -> None:
    """With a ``"VERB path"`` override, a wordless read is named by it."""
    client = _client(tmp_path, _get("get_root", '"api/v1/"') + _get("get_item", 't"v1/{key}"'))
    snapshot = _snapshot(tmp_path, [("GET", "/api/v1/"), ("GET", "/v1/{key}")])
    assert len(check_names(client, snapshot)) == 2  # noqa: PLR2004 -- one problem per wordless read
    assert check_names(client, snapshot, overrides={"GET /api/v1/": "get_root", "GET /v1/{key}": "get_item"}) == []


def test_wordless_read_without_source_needs_a_path_override(tmp_path: Path) -> None:
    """Without a docs source the client's own wordless path is reported the same way."""
    client = _client(tmp_path, _get("get_root", '"v2/"'))
    problems = check_names(client, _snapshot(tmp_path, [], source=None, reason="no reference"))
    assert len(problems) == 1, problems
    assert "derives no name" in problems[0]
    assert check_names(client, _snapshot(tmp_path, [], source=None, reason="x"), overrides={"GET v2": "get_root"}) == []


def test_no_general_singularisation(tmp_path: Path) -> None:
    """``/v3/quotes/{ticker}`` alone is ``get_quotes``: no collision, no singular."""
    client = _client(tmp_path, _get("get_quotes", 't"v3/quotes/{ticker}"'))
    assert check_names(client, _snapshot(tmp_path, [("GET", "/v3/quotes/{ticker}")])) == []


def test_misnamed_read_reported(tmp_path: Path) -> None:
    """A read whose name is not its path's name is reported with the expected name."""
    client = _client(tmp_path, _get("quotes", 't"v3/quotes/{ticker}"'))
    (problem,) = check_names(client, _snapshot(tmp_path, [("GET", "/v3/quotes/{ticker}")]))
    assert "quotes" in problem
    assert "should be named get_quotes" in problem


def test_override_renames(tmp_path: Path) -> None:
    """An override maps the path's name to the method's name."""
    client = _client(tmp_path, _get("get_last_quote", 't"v3/quotes/{ticker}"'))
    snapshot = _snapshot(tmp_path, [("GET", "/v3/quotes/{ticker}")])
    assert check_names(client, snapshot, overrides={"get_quotes": "get_last_quote"}) == []


def test_undocumented_method_reported(tmp_path: Path) -> None:
    """A method whose endpoint the snapshot does not list is reported."""
    body = _get("get_quotes", '"v3/quotes"') + _get("get_trades", '"v3/trades"')
    (problem,) = check_names(_client(tmp_path, body), _snapshot(tmp_path, [("GET", "/v3/quotes")]))
    assert "get_trades" in problem
    assert "GET v3/trades" in problem
    assert "not in the snapshot" in problem


def test_missing_method_reported(tmp_path: Path) -> None:
    """A documented GET with no method is reported."""
    client = _client(tmp_path, _get("get_quotes", '"v3/quotes"'))
    (problem,) = check_names(client, _snapshot(tmp_path, [("GET", "/v3/quotes"), ("GET", "/v3/trades")]))
    assert "GET /v3/trades" in problem
    assert "has no method" in problem


def test_documented_write_without_method_not_reported(tmp_path: Path) -> None:
    """A documented POST that is not a read needs no method."""
    client = _client(tmp_path, _get("get_quotes", '"v3/quotes"'))
    assert check_names(client, _snapshot(tmp_path, [("GET", "/v3/quotes"), ("POST", "/v3/orders")])) == []


def test_stale_override_reported(tmp_path: Path) -> None:
    """An override whose key is no endpoint's name is reported."""
    client = _client(tmp_path, _get("get_quotes", '"v3/quotes"'))
    (problem,) = check_names(client, _snapshot(tmp_path, [("GET", "/v3/quotes")]), overrides={"get_trades": "trades"})
    assert "get_trades" in problem
    assert "stale" in problem


def test_unexempt_write_reported(tmp_path: Path) -> None:
    """A non-GET method in neither ``exempt_writes`` nor ``post_reads`` is reported; exempting it clears it."""
    body = (
        '    async def create_order(self, b: B) -> O:\n        return await self.post("v2/orders", body=b, expect=X)\n'
    )
    client = _client(tmp_path, body)
    snapshot = _snapshot(tmp_path, [("POST", "/v2/orders")])
    (problem,) = check_names(client, snapshot)
    assert "create_order" in problem
    assert "exempt_writes" in problem
    assert check_names(client, snapshot, exempt_writes=("create_order",)) == []


def test_post_read_is_named_as_a_read(tmp_path: Path) -> None:
    """A ``post_reads`` method is checked as a read, and its documented POST needs a method."""
    body = '    async def get_search(self, b: B) -> O:\n        return await self.post("v1/search", body=b, expect=X)\n'
    snapshot = _snapshot(tmp_path, [("POST", "/v1/search")])
    assert check_names(_client(tmp_path, body), snapshot, post_reads=("get_search",)) == []
    renamed = body.replace("get_search", "search")
    (problem,) = check_names(_client(tmp_path, renamed), snapshot, post_reads=("search",))
    assert "should be named get_search" in problem


def test_null_source_skips_docs_comparison(tmp_path: Path) -> None:
    """With ``source: null`` the names are still checked, but not against the snapshot's endpoints."""
    body = _get("get_quote_summary", 't"v10/finance/quoteSummary/{symbol}"') + _get("chart", 't"v8/finance/chart"')
    snapshot = _snapshot(tmp_path, [], source=None, reason="the API publishes no reference")
    (problem,) = check_names(_client(tmp_path, body), snapshot, filler=DEFAULT_FILLER | {"finance"})
    assert "chart" in problem
    assert "should be named get_chart" in problem


def test_null_source_needs_reason(tmp_path: Path) -> None:
    """A snapshot with ``source: null`` and no reason is rejected."""
    client = _client(tmp_path, _get("get_quotes", '"v3/quotes"'))
    with pytest.raises(SnapshotError, match="reason"):
        check_names(client, _snapshot(tmp_path, [], source=None))


def test_base_url_prefix_matches_on_a_segment_boundary(tmp_path: Path) -> None:
    """R16: a client path relative to a base URL holding ``/api/v3`` matches the snapshot's full path."""
    client = _client(tmp_path, _get("get_quotes", 't"/quotes/{ticker}/"'))
    assert check_names(client, _snapshot(tmp_path, [("GET", "/api/v3/quotes/{symbol}")])) == []
    other = _client(tmp_path, _get("get_quotes", 't"otes/{ticker}"'))
    problems = check_names(other, _snapshot(tmp_path, [("GET", "/api/v3/quotes/{symbol}")]))
    assert any("not in the snapshot" in p for p in problems), problems


def test_ambiguous_match_reported(tmp_path: Path) -> None:
    """R16: a method matching more than one documented path is a problem, not a pick."""
    client = _client(tmp_path, _get("get_quotes", '"quotes"'))
    snapshot = _snapshot(tmp_path, [("GET", "/v1/quotes"), ("GET", "/v2/quotes")])
    problems = check_names(client, snapshot)
    assert any("more than one" in p and "/v1/quotes" in p and "/v2/quotes" in p for p in problems), problems


def test_exact_match_wins_over_suffix_matches(tmp_path: Path) -> None:
    """A documented path equal to the client's is the match, even when longer documented paths end with it too."""
    client = _client(tmp_path, _get("get_quotes", '"quotes"'))
    snapshot = _snapshot(tmp_path, [("GET", "/quotes"), ("GET", "/v2/quotes")])
    assert check_names(client, snapshot, overrides={"GET /v2/quotes": "get_v2_quotes"}) == [
        "the documented read GET /v2/quotes has no method"
    ]


def test_documented_root_read_beside_other_reads_passes_with_its_override(tmp_path: Path) -> None:
    """R29's override for a root ``GET /`` is enough: the root path matches the documented root, not every path."""
    body = _get("get_root", '"/"') + _get("get_filings", '"v1/filings"')
    snapshot = _snapshot(tmp_path, [("GET", "/"), ("GET", "/v1/filings")])
    assert check_names(_client(tmp_path, body), snapshot, overrides={"GET /": "get_root"}) == []


# Fix round 1: unreadable paths, R17 path overrides, R18 names from the documented path


def test_unreadable_path_reported_with_a_source(tmp_path: Path) -> None:
    """A method whose path cannot be read is named, and the missing-method line counts it."""
    body = "    async def get_quotes(self, t: str) -> X:\n        return await self.get(self._url(t), expect=X)\n"
    problems = check_names(_client(tmp_path, body), _snapshot(tmp_path, [("GET", "/v3/quotes/{t}")]))
    assert problems == [
        (
            "get_quotes calls self.get with a path that is not a string, t-string or module-level constant (or a "
            "one-level delegate to one); spell the path as one of those so its name can be checked"
        ),
        "the documented read GET /v3/quotes/{t} has no method (1 method has an unreadable path)",
    ]


def test_unreadable_path_reported_with_a_null_source(tmp_path: Path) -> None:
    """With ``source: null`` an f-string path is reported, so a misnamed read cannot pass silently."""
    body = '    async def quotez(self, t: str) -> X:\n        return await self.get(f"v3/quotes/{t}", expect=X)\n'
    snapshot = _snapshot(tmp_path, [], source=None, reason="no reference")
    (problem,) = check_names(_client(tmp_path, body), snapshot)
    assert problem.startswith("quotez calls self.get with a path that is not a string")


def test_unreadable_path_through_a_delegate_reported(tmp_path: Path) -> None:
    """A one-level delegate whose leg's path cannot be read is reported, naming the leg's call."""
    body = (
        "    async def get_d(self, url: str) -> D:\n        return await self._d(url)\n\n"
        "    async def _d(self, url: str) -> D:\n        return await self.get(url.strip(), expect=X)\n"
    )
    snapshot = _snapshot(tmp_path, [], source=None, reason="no reference")
    (problem,) = check_names(_client(tmp_path, body), snapshot)
    assert problem.startswith("get_d calls self.get (through self._d) with a path that is not")


def test_helper_call_is_not_an_unreadable_endpoint(tmp_path: Path) -> None:
    """A public method calling a sibling that makes no request is no endpoint at all."""
    body = "    def label(self) -> str:\n        return self._label()\n\n"
    body += "    def _label(self) -> str:\n        return 'x'\n"
    snapshot = _snapshot(tmp_path, [], source=None, reason="no reference")
    assert check_names(_client(tmp_path, body), snapshot) == []


@pytest.mark.parametrize(
    ("list_path", "item_path", "list_name", "item_name"),
    [
        ("v1/series", "v1/series/{i}", "get_series", "get_series_item"),
        ("v2/stocks/bars", "v2/stocks/{s}/bars", "get_stocks_bars", "get_stock_bars"),
    ],
)
def test_collision_reported_and_resolved_by_a_path_override(
    tmp_path: Path, list_path: str, item_path: str, list_name: str, item_name: str
) -> None:
    """R17: two read paths deriving one name are reported, and a ``"VERB path"`` override resolves them."""
    key = f"GET {item_path}"
    body = _get(list_name, f't"{list_path}"') + _get(item_name, f't"{item_path}"')
    snapshot = _snapshot(tmp_path, [("GET", f"/{list_path}"), ("GET", f"/{item_path}")])
    problems = check_names(_client(tmp_path, body), snapshot)
    collision = f'{list_path} and {item_path} both name {list_name}; add an override keyed "{key}"'
    assert collision in problems, problems
    assert all("override keyed" not in p or key in p for p in problems), problems
    assert check_names(_client(tmp_path, body), snapshot, overrides={key: item_name}) == []


def test_path_override_wins_over_a_name_override(tmp_path: Path) -> None:
    """R17: a ``"VERB path"`` key wins over a name key for its endpoint; the path is normalised per R16."""
    body = _get("get_last", 't"v3/quotes/{ticker}"')
    snapshot = _snapshot(tmp_path, [("GET", "/v3/quotes/{ticker}")])
    overrides = {"get_quotes": "get_other", "get /v3/quotes/{t}/": "get_last"}
    assert check_names(_client(tmp_path, body), snapshot, overrides=overrides) == []


def test_stale_path_override_reported(tmp_path: Path) -> None:
    """R17: a ``"VERB path"`` key matching no endpoint is stale."""
    client = _client(tmp_path, _get("get_quotes", '"v3/quotes"'))
    (problem,) = check_names(client, _snapshot(tmp_path, [("GET", "/v3/quotes")]), overrides={"GET v3/trades": "x"})
    assert "'GET v3/trades'" in problem
    assert "stale" in problem


def test_name_from_the_documented_path(tmp_path: Path) -> None:
    """R18: a method matching one documented endpoint is named from the documented path."""
    client = _client(tmp_path, _get("get_benzinga_analyst_insights", '"v1/analyst-insights"'))
    snapshot = _snapshot(tmp_path, [("GET", "/benzinga/v1/analyst-insights")])
    assert check_names(client, snapshot) == []
    wrong = _client(tmp_path, _get("get_analyst_insights", '"v1/analyst-insights"'))
    (problem,) = check_names(wrong, snapshot)
    assert "should be named get_benzinga_analyst_insights" in problem


# R26: the project's [tool.headgate-verify] lists, read from the pyproject nearest the package


def _pyproject(tmp_path: Path, table: str) -> None:
    (tmp_path / "pyproject.toml").write_text(f"[tool.headgate-verify]\n{table}\n", encoding="utf-8")


def test_project_filler_words_change_a_derived_name(tmp_path: Path) -> None:
    """R26: ``filler-words`` in the package's pyproject drops a word; an explicit ``filler`` still wins."""
    _pyproject(tmp_path, 'filler-words = ["finance"]')
    client = _client(tmp_path, _get("get_quote_summary", 't"v10/finance/quoteSummary/{symbol}"'))
    snapshot = _snapshot(tmp_path, [("GET", "/v10/finance/quoteSummary/{symbol}")])

    assert check_names(client, snapshot) == []
    (problem,) = check_names(client, snapshot, filler=DEFAULT_FILLER)
    assert "should be named get_finance_quote_summary" in problem


def test_project_post_reads_make_a_post_a_read(tmp_path: Path) -> None:
    """R26: ``post-reads`` in the package's pyproject makes a POST a read; an explicit ``post_reads`` still wins."""
    _pyproject(tmp_path, 'post-reads = ["get_search"]')
    body = '    async def get_search(self, b: B) -> O:\n        return await self.post("v1/search", body=b, expect=X)\n'
    client = _client(tmp_path, body)
    snapshot = _snapshot(tmp_path, [("POST", "/v1/search")])

    assert check_names(client, snapshot) == []
    (problem,) = check_names(client, snapshot, post_reads=())
    assert "exempt_writes" in problem


def test_no_project_lists_keep_the_defaults(tmp_path: Path) -> None:
    """R26: with no pyproject table, ``finance`` is not filler and a POST is not a read."""
    _pyproject(tmp_path, "")
    client = _client(tmp_path, _get("get_quote_summary", 't"v10/finance/quoteSummary/{symbol}"'))
    (problem,) = check_names(client, _snapshot(tmp_path, [("GET", "/v10/finance/quoteSummary/{symbol}")]))
    assert "should be named get_finance_quote_summary" in problem
