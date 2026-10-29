# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Tests for names from the vendor's spec: one table per rule, then the name check and the review over a client.

The operationIds are the shapes measured across eighteen vendors' official specs; each case names the rule it holds.
"""

import json
from typing import TYPE_CHECKING

import pytest

from headgate_verify import review
from headgate_verify.endpoints import read_requests
from headgate_verify.naming import SpecName, check_names, id_words, review_names, spec_name, spec_namespace
from headgate_verify.snapshot import Endpoint

if TYPE_CHECKING:
    from pathlib import Path

USAGE_ERROR = 2


def _named(verb: str, path: str, operation_id: str, **details: str) -> Endpoint:
    return Endpoint(verb, path, operation_id, **details)


# id_words


@pytest.mark.parametrize(
    ("text", "words"),
    [
        ("listClients", ["list", "clients"]),
        ("getIPOsCalendar", ["get", "ipos", "calendar"]),
        ("HTTPServerStatus", ["http", "server", "status"]),
        ("get-referral-codes", ["get", "referral", "codes"]),
        ("Create an Order", ["create", "an", "order"]),
    ],
)
def test_id_words(text: str, words: list[str]) -> None:
    """camelCase, an acronym run, an acronym's plural, kebab-case and a summary each split into lower-case words."""
    assert id_words(text) == words


# what the endpoint states, and the verb is the first word it does not


@pytest.mark.parametrize(
    ("endpoint", "models", "name"),
    [
        (_named("GET", "/api/v1/clients/", "listClients"), (), "get_clients"),
        (_named("GET", "/api/v1/clients/{id}/", "retrieveClient"), (), "get_client"),
        (_named("GET", "/v2/stocks/bars/latest", "StockLatestBars"), (), "get_stock_latest_bars"),
        (
            _named("GET", "/constants/filing/governmententities/", "listGovernmentEntities"),
            (),
            "get_government_entities",
        ),
        (_named("GET", "/v2/account", "getAccountSummary"), (), "get_account"),
        (_named("GET", "/v2/account", "getAccountSummary"), ("AccountSummary",), "get_account_summary"),
        (
            _named("GET", "/v2/account", "getAccountSummary", response_schema="AccountSummary"),
            (),
            "get_account_summary",
        ),
        (_named("GET", "/v2/stream/quotes", "streamQuotes"), (), "get_stream_quotes"),
    ],
    ids=[
        "verb-first",
        "item",
        "no-verb",
        "glued-path-word",
        "unstated-noun",
        "model-name",
        "schema-name",
        "verb-in-path",
    ],
)
def test_a_read_keeps_the_words_the_endpoint_states(endpoint: Endpoint, models: tuple[str, ...], name: str) -> None:
    """A read is ``get`` and the id's stated words: the path's, a glued piece of one, a model's or a schema's name."""
    assert spec_name(endpoint, models=models).name == name


@pytest.mark.parametrize(
    ("endpoint", "name"),
    [
        (_named("POST", "/v1/orders", "postOrder", summary="Create an Order"), "create_order"),
        (_named("PUT", "/v1/watchlists/{id}", "putWatchlist", summary="Update Watchlist by Id"), "update_watchlist"),
        (_named("POST", "/v1/orders", "postOrder", summary="Order placement"), "post_order"),
        (_named("POST", "/v1/orders", "postOrder"), "post_order"),
        (_named("DELETE", "/v1/orders/{id}", "cancelOrder", summary="Delete an order"), "cancel_order"),
        (_named("POST", "/v1/locates", "createLocate", request_schema="CreateLocateRequest"), "create_locate"),
        (_named("POST", "/2/calls/{id}/leave", "leaveCall", summary="Leave a call"), "leave_call"),
        (_named("POST", "/v3/orders/batch_cancel", "CancelOrders"), "cancel_orders"),
        (_named("POST", "/2/media/upload", "mediaUpload"), "upload_media"),
    ],
    ids=[
        "summary-verb",
        "summary-verb-put",
        "summary-noun-phrase",
        "no-summary",
        "id-verb-kept",
        "schema-repeats-verb",
        "action-path",
        "action-glued",
        "action-trailing",
    ],
)
def test_a_write_takes_its_verb(endpoint: Endpoint, name: str) -> None:
    """A write's verb is the id's first unstated word; the summary's when the id's only repeats the HTTP verb."""
    assert spec_name(endpoint, write=True).name == name


def test_a_write_with_no_verb_gives_no_name() -> None:
    """An id and summary whose every word the endpoint states, off an action path, name no verb."""
    result = spec_name(_named("POST", "/v1/orders/batch", "orders"), write=True)
    assert result == SpecName(rejected="the operationId 'orders' and its summary name no verb")


# the namespace


def _ids(*pairs: tuple[str, str]) -> list[Endpoint]:
    return [_named(verb, f"/{index}", operation_id) for index, (verb, operation_id) in enumerate(pairs)]


@pytest.mark.parametrize(
    ("endpoints", "namespace"),
    [
        (
            _ids(
                ("GET", "RetailBrokerageApi_GetAccounts"),
                ("GET", "RetailBrokerageApi_GetOrder"),
                ("GET", "RetailBrokerageApi_ListOrders"),
                ("POST", "RetailBrokerageApi_PostOrder"),
                ("DELETE", "RetailBrokerageApi_CancelOrders"),
            ),
            ("retail", "brokerage", "api"),
        ),
        (
            _ids(
                ("GET", "engineGetA"),
                ("GET", "engineGetB"),
                ("GET", "engineGetC"),
                ("GET", "engineGetE"),
                ("GET", "other"),
                ("POST", "enginePostD"),
            ),
            ("engine",),
        ),
        (
            _ids(
                ("GET", "getA"), ("GET", "getB"), ("GET", "getC"), ("GET", "getD"), ("POST", "getE"), ("POST", "makeF")
            ),
            (),
        ),
        (_ids(("GET", "getA"), ("GET", "getB"), ("GET", "getC"), ("GET", "getD"), ("GET", "getE")), ()),
        (_ids(("GET", "nsA"), ("GET", "nsB"), ("POST", "nsC"), ("POST", "nsD")), ()),
    ],
    ids=["several-words", "one-word", "a-verb-is-no-namespace", "one-http-verb", "too-few-ids"],
)
def test_spec_namespace(endpoints: list[Endpoint], namespace: tuple[str, ...]) -> None:
    """The namespace leads 80% of each HTTP verb's ids, over more than one verb, in five ids or more."""
    assert spec_namespace(endpoints) == namespace


def test_the_namespace_is_stripped_from_the_id_and_the_summary() -> None:
    """``retailPostOrder`` with the summary "Retail: Create Order" is ``create_order``."""
    endpoint = _named("POST", "/orders", "retailPostOrder", summary="Retail: Create Order")
    assert spec_name(endpoint, write=True, namespace=("retail",)).name == "create_order"
    assert spec_name(_named("GET", "/orders", "retailListOrders"), namespace=("retail",)).name == "get_orders"


# the gate


@pytest.mark.parametrize(
    ("endpoint", "reason"),
    [
        (_named("GET", "/api/etfs/{ticker}/info", "PublicApi.EtfController.info"), "a code path"),
        (_named("GET", "/stocks/v1/short-interest", "get_stocks_v1_short-interest"), "the path written out"),
        (_named("GET", "/items/{item_id}", "read_items_items__item_id__get"), "the path written out"),
        (_named("GET", "/stocks/v1/exchanges", "get_stocks_v1_exchanges"), "the path written out"),
        (_named("GET", "/orders/{order_id}", "getOrdersOrderId"), "spells the path hole {order_id}"),
        (_named("GET", "/accounts/{id}", "getAccountsId"), "spells the path hole {id}"),
        (_named("GET", "/v1/stuff", "doThing"), "states no word of the endpoint"),
        (_named("GET", "/v1/stuff", ""), "no operationId"),
    ],
    ids=[
        "code-path",
        "path-written-out",
        "fastapi-default",
        "path-with-version",
        "multi-word-hole",
        "id-hole",
        "no-word",
        "no-id",
    ],
)
def test_the_gate_rejects(endpoint: Endpoint, reason: str) -> None:
    """A code path, the path written out, a hole spelled as words, or no stated word gives no name, and says why."""
    result = spec_name(endpoint)
    assert result.name == ""
    assert reason in result.rejected


@pytest.mark.parametrize(
    ("endpoint", "name"),
    [
        (_named("GET", "/orders/{order_id}", "getOrderByOrderId"), "get_order"),
        (_named("GET", "/v2/news/{ticker}", "getTickerNews"), "get_news"),
        (_named("GET", "/v2/positions/{symbol}", "GetOpenPosition"), "get_position"),
        (_named("GET", "/v2/assets/{id}", "getSingleAsset"), "get_asset"),
    ],
    ids=["hole-after-a-link-word", "one-word-hole", "unstated-open", "unstated-single"],
)
def test_the_gate_passes_and_the_filter_drops_unstated_words(endpoint: Endpoint, name: str) -> None:
    """A hole after an unstated link word (``by``) passes the gate; a word the endpoint never states is dropped."""
    assert spec_name(endpoint).name == name


# singular or plural


@pytest.mark.parametrize(
    ("endpoint", "name"),
    [
        (_named("GET", "/markets", "getMarket"), "get_markets"),
        (_named("GET", "/market", "listMarkets"), "get_market"),
        (_named("GET", "/2010-04-01/Accounts/{sid}/Applications.json", "ListApplication"), "get_applications"),
        (_named("GET", "/quote/latest", "getLatestQuote", response_shape="array"), "get_latest_quotes"),
        (_named("GET", "/positions/{id}", "listPositions", response_shape="object"), "get_positions"),
        (_named("GET", "/data", "getData", response_shape="array"), "get_data"),
        (_named("GET", "/census/{year}", "getCensus", response_shape="array"), "get_census"),
        (_named("GET", "/quote/latest", "getLatestQuote", response_shape="object"), "get_latest_quote"),
    ],
    ids=["path-plural", "path-singular", "path-extension", "array", "object-says-nothing", "data", "census", "object"],
)
def test_a_read_takes_its_number(endpoint: Endpoint, name: str) -> None:
    """The last noun takes the path's last word's number, else a plural for a JSON array; inflect never singularises."""
    assert spec_name(endpoint).name == name


# the call-shape prefix and the vendor's word order


@pytest.mark.parametrize(
    ("prefix", "endpoint", "name"),
    [
        ("walk", _named("GET", "/v1/orders", "listOrders"), "walk_orders"),
        ("stream", _named("GET", "/v2/stream/quotes", "streamQuotes"), "stream_quotes"),
        ("fetch", _named("GET", "/v1/reports/{id}/pdf", "getReportPdf"), "fetch_report_pdf"),
        ("get", _named("GET", "/v1/bars/{symbol}/latest", "getLatestBars"), "get_latest_bars"),
        ("get", _named("GET", "/v2/orders", "getOrdersV2"), "get_orders"),
    ],
    ids=["walk", "stream", "fetch", "vendor-order", "version-token"],
)
def test_the_prefix_and_the_word_order(prefix: str, endpoint: Endpoint, name: str) -> None:
    """A read starts with the caller's call shape; the id's words keep the vendor's order; a version token goes."""
    assert spec_name(endpoint, prefix=prefix).name == name


def test_full_keeps_every_id_word() -> None:
    """``full`` keeps the words the filter drops, for a name that collides."""
    assert spec_name(_named("GET", "/v2/positions", "getAllOpenPositions")) == SpecName(
        "get_positions", "get_all_open_positions"
    )


# check_names and review_names over a client


def _client(tmp_path: Path, methods: list[tuple[str, str, str]]) -> Path:
    """Write a client whose methods are ``(name, call, return annotation)``: ``call`` is ``get "v1/x"`` style."""
    lines = ["class Client(AsyncBaseClient):"]
    for name, call, returns in methods:
        verb, _, path = call.partition(" ")
        lines += [
            f"    async def {name}(self) -> {returns}:",
            f"        return await self.{verb}({path}, expect=X)",
            "",
        ]
    path = tmp_path / "client.py"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _snapshot(tmp_path: Path, endpoints: list[Endpoint], *, details: bool = True) -> Path:
    keys = ("verb", "path", "operation_id", "summary", "request_schema", "response_schema", "response_shape")
    rows = [
        {key: getattr(endpoint, key) for key in (keys if details else keys[:2])}
        for endpoint in sorted(endpoints, key=lambda endpoint: (endpoint.path, endpoint.verb))
    ]
    path = tmp_path / "docs_paths.json"
    data = {"source": "https://api.example/openapi.json", "retrieved": "2026-10-28", "reason": None, "endpoints": rows}
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


_ORDERS = [
    _named("GET", "/v1/orders", "listOrders"),
    _named("GET", "/v1/constants/order/ordertypes", "listOrderTypes", response_shape="array"),
    _named("POST", "/v1/orders", "postOrder", summary="Create an Order"),
]


def test_adding_a_spec_snapshot_switches_to_spec_names(tmp_path: Path) -> None:
    """A path-named client passes a plain snapshot; once the snapshot carries operationIds the spec names it."""
    path_named = [
        ("get_orders", 'get "v1/orders"', "list[Order]"),
        ("get_constants_order_ordertypes", 'get "v1/constants/order/ordertypes"', "list[Constant]"),
        ("place_order", 'post "v1/orders"', "Order"),
    ]
    client = _client(tmp_path, path_named)
    assert check_names(client, _snapshot(tmp_path, _ORDERS, details=False), exempt_writes=["place_order"]) == []
    assert check_names(client, _snapshot(tmp_path, _ORDERS), exempt_writes=["place_order"]) == [
        (
            "get_constants_order_ordertypes reads GET v1/constants/order/ordertypes and should be named "
            "get_order_types (from the spec's operationId 'listOrderTypes') (or add an override with a reason)"
        ),
        (
            "place_order sends POST v1/orders and should be named create_order (from the spec's operationId "
            "'postOrder') (or add an override with a reason)"
        ),
    ]
    spec_named = [path_named[0], ("get_order_types", path_named[1][1], ""), ("create_order", path_named[2][1], "")]
    assert (
        check_names(_client(tmp_path, spec_named), _snapshot(tmp_path, _ORDERS), exempt_writes=["create_order"]) == []
    )


def test_a_colliding_spec_name_keeps_its_words_then_takes_the_path(tmp_path: Path) -> None:
    """Two filtered names that collide each keep every id word; two that still collide take their paths' names."""
    endpoints = [
        _named("GET", "/v1/positions", "getAllPositions"),
        _named("GET", "/v1/positions/{symbol}", "getPositions"),
        _named("GET", "/v1/trades", "listTrades"),
        _named("GET", "/v1/trades/{id}", "getTrades"),
    ]
    methods = [
        ("get_all_positions", 'get "v1/positions"', ""),
        ("get_positions", 'get t"v1/positions/{symbol}"', ""),
        ("get_trades", 'get "v1/trades"', ""),
        ("get_trade", 'get t"v1/trades/{trade_id}"', ""),
    ]
    snapshot = _snapshot(tmp_path, endpoints)
    assert check_names(_client(tmp_path, methods), snapshot) == []
    reason = "its spec name get_trades is another endpoint's too"
    assert review_names(_client(tmp_path, methods), snapshot) == [
        f"{name} reads GET {path} by its path's name {name}: {reason}; if that name does not say what the endpoint "
        f'does, name it from the docs with an override keyed "GET {path}" with a reason'
        for name, path in [("get_trade", "/v1/trades/{id}"), ("get_trades", "/v1/trades")]
    ]


def test_return_models_are_stated(tmp_path: Path) -> None:
    """The client's return model names count as stated words, so ``AccountSummary`` keeps ``summary``."""
    endpoints = [_named("GET", "/v2/account", "getAccountSummary")]
    snapshot = _snapshot(tmp_path, endpoints)
    assert check_names(_client(tmp_path, [("get_account", 'get "v2/account"', "Account")]), snapshot) == []
    summary = [("get_account_summary", 'get "v2/account"', "AccountSummary | None")]
    assert check_names(_client(tmp_path, summary), snapshot) == []


def test_overrides_win_over_spec_names(tmp_path: Path) -> None:
    """A ``"VERB path"`` key or the spec name as a key renames; an override of a name nothing derives is stale."""
    snapshot = _snapshot(tmp_path, _ORDERS[:2])
    methods = [("get_orders", 'get "v1/orders"', ""), ("get_types", 'get "v1/constants/order/ordertypes"', "")]
    client = _client(tmp_path, methods)
    assert check_names(client, snapshot, overrides={"get_order_types": "get_types"}) == []
    assert check_names(client, snapshot, overrides={"GET /v1/constants/order/ordertypes": "get_types"}) == []
    assert check_names(client, snapshot, overrides={"get_constants_order_ordertypes": "get_types"}) == [
        (
            "get_types reads GET v1/constants/order/ordertypes and should be named get_order_types (from the spec's "
            "operationId 'listOrderTypes') (or add an override with a reason)"
        ),
        (
            "the override 'get_constants_order_ordertypes' -> 'get_types' is stale: no endpoint is named "
            "get_constants_order_ordertypes"
        ),
    ]


def test_a_write_the_spec_does_not_name_is_unchecked(tmp_path: Path) -> None:
    """A write whose id the gate rejects keeps its own name, and the review lists it."""
    endpoints = [_named("POST", "/v1/orders/batch", "orders"), _named("GET", "/v1/orders", "listOrders")]
    client = _client(tmp_path, [("submit", 'post "v1/orders/batch"', ""), ("get_orders", 'get "v1/orders"', "")])
    snapshot = _snapshot(tmp_path, endpoints)
    assert check_names(client, snapshot, exempt_writes=["submit"]) == []
    assert review_names(client, snapshot, exempt_writes=["submit"]) == [
        (
            "submit sends POST /v1/orders/batch, which no rule names: the operationId 'orders' and its summary name no "
            "verb; check its name"
        )
    ]


def test_review_lists_what_the_rules_cannot_name(tmp_path: Path) -> None:
    """A rejected id, a wordless path, two methods on one path and a URL argument are listed; an override clears one."""
    endpoints = [
        _named("GET", "/", "getRoot"),
        _named("GET", "/api/stock/{ticker}/info", "PublicApi.TickerController.info"),
        _named("GET", "/v1/quotes", "listQuotes"),
    ]
    methods = [
        ("get_root", 'get "/"', ""),
        ("get_stock_info", 'get t"api/stock/{ticker}/info"', ""),
        ("get_quotes", 'get "v1/quotes"', ""),
        ("get_quotes_csv", 'get "v1/quotes"', ""),
        ("get_url", "get url", ""),
    ]
    client = _client(tmp_path, methods)
    snapshot = _snapshot(tmp_path, endpoints)
    assert review_names(client, snapshot, exempt_writes=["get_url"]) == [
        (
            "get_quotes and get_quotes_csv all send GET /v1/quotes; one path names one method, so check each "
            "against the docs"
        ),
        (
            'get_root reads GET /, whose path has no word; name it from the docs with an override keyed "GET /" with a '
            "reason"
        ),
        (
            "get_stock_info reads GET /api/stock/{ticker}/info by its path's name get_stock_info: the operationId "
            "'PublicApi.TickerController.info' is not used: it is a code path (it holds a '.'); if that name does not "
            'say what the endpoint does, name it from the docs with an override keyed "GET /api/stock/{ticker}/info" '
            "with a reason"
        ),
        "get_url calls self.get with a path that cannot be read, so its name is unchecked; check it against the docs",
    ]
    overrides = {"GET /": "get_root", "GET /api/stock/{}/info": "get_stock_info"}
    left = review_names(client, snapshot, overrides=overrides, exempt_writes=["get_url"])
    assert [line.split(" ", 1)[0] for line in left] == ["get_quotes", "get_url"]


def test_read_requests_keeps_the_return_annotation(tmp_path: Path) -> None:
    """Each request carries its public method's return annotation, ``""`` when it has none."""
    client = _client(tmp_path, [("get_a", 'get "v1/a"', "Paginated[Page[A], A]")])
    client.write_text(
        client.read_text(encoding="utf-8") + "\n    async def get_b(self):\n        return await self.get('b')\n",
        encoding="utf-8",
    )
    requests = read_requests(client)
    assert requests["get_a"].returns == "Paginated[Page[A], A]"
    assert requests["get_b"].returns == ""


# headgate-names


def _package(tmp_path: Path, tables: str) -> Path:
    _client(tmp_path, [("get_stock_info", 'get t"api/stock/{ticker}/info"', "")])
    _snapshot(tmp_path, [_named("GET", "/api/stock/{ticker}/info", "PublicApi.TickerController.info")])
    test_module = tmp_path / "test_method_names.py"
    test_module.write_text(f"from pathlib import Path\n\nPACKAGE = Path({str(tmp_path)!r})\n{tables}", encoding="utf-8")
    return test_module


def test_headgate_names_prints_the_review(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The command reads the test module's tables, prints one line per name to review, and exits 0."""
    assert review.main([str(_package(tmp_path, ""))]) == 0
    out, err = capsys.readouterr()
    assert out.startswith("get_stock_info reads GET /api/stock/{ticker}/info by its path's name get_stock_info")
    assert err == "1 name(s) to review\n"
    assert review.main([str(_package(tmp_path, 'OVERRIDES = {"GET /api/stock/{}/info": "get_stock_info"}\n'))]) == 0
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    ("text", "fragment"),
    [
        ("PACKAGE = 'nope'\n", "defines no PACKAGE"),
        ("import nowhere_at_all\n", "cannot be run"),
        ("x = (\n", "cannot be run"),
    ],
)
def test_headgate_names_usage_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], text: str, fragment: str
) -> None:
    """A module with no ``PACKAGE`` path, or one that cannot run, is a usage error."""
    module = tmp_path / "test_method_names.py"
    module.write_text(text, encoding="utf-8")
    assert review.main([str(module)]) == USAGE_ERROR
    assert fragment in capsys.readouterr().err


def test_headgate_names_reports_a_broken_snapshot(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A snapshot that breaks its schema is a usage error naming why."""
    module = _package(tmp_path, "")
    (tmp_path / "docs_paths.json").write_text("{", encoding="utf-8")
    assert review.main([str(module)]) == USAGE_ERROR
    assert "not valid JSON" in capsys.readouterr().err


@pytest.mark.parametrize(("argv", "code"), [(["--help"], 0), ([], USAGE_ERROR)])
def test_headgate_names_usage(argv: list[str], code: int) -> None:
    """``--help`` exits 0 and a missing argument exits 2, never raising ``SystemExit``."""
    assert review.main(argv) == code
