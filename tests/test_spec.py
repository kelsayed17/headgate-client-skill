# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Tests for writing the docs snapshot from an API spec: parsing, the operation details, fetching, the command."""

import json
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

import pytest

from headgate_verify import spec
from headgate_verify.snapshot import DocsSnapshot, Endpoint, SnapshotError, dump_snapshot, load_snapshot

if TYPE_CHECKING:
    from pathlib import Path

USAGE_ERROR = 2
_OPENAPI = {
    "openapi": "3.0.2",
    "paths": {
        "/v1/orders": {
            "parameters": [],
            "get": {
                "operationId": "listOrders",
                "summary": "List  all\n orders",
                "responses": {
                    "200": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/Orders"}}}}
                },
            },
            "post": {
                "operationId": "postOrder",
                "summary": "Create an Order",
                "requestBody": {
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/OrderRequest"}}}
                },
                "responses": {
                    "201": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/Order"}}}}
                },
            },
        },
        "/v1/orders/{id}": {
            "get": {
                "operationId": "getOrder",
                "responses": {"200": {"content": {"text/plain": {"schema": {"type": "string"}}}}},
            },
            "delete": {"responses": {"204": {}}},
        },
    },
    "components": {
        "schemas": {
            "Orders": {"type": "array", "items": {"$ref": "#/components/schemas/Order"}},
            "Order": {"type": "object", "properties": {"id": {"type": "string"}}},
            "OrderRequest": {"properties": {}},
        }
    },
}
_EXPECTED = (
    Endpoint("GET", "/v1/orders", "listOrders", "List all orders", "", "Orders", "array"),
    Endpoint("POST", "/v1/orders", "postOrder", "Create an Order", "OrderRequest", "Order", "object"),
    Endpoint("DELETE", "/v1/orders/{id}"),
    Endpoint("GET", "/v1/orders/{id}", "getOrder"),
)


# parse_documents and endpoints


def test_parse_json() -> None:
    """A JSON document is read as it is, and every operation carries its details."""
    assert spec.endpoints(spec.parse_documents(json.dumps(_OPENAPI))) == _EXPECTED


def test_parse_yaml() -> None:
    """A YAML document reads the same; a numeric response code is a success too."""
    raw = "swagger: '2.0'\npaths:\n  /a:\n    get:\n      operationId: getA\n      responses:\n        200:\n"
    raw += "          schema: {type: array, items: {type: string}}\n"
    assert spec.endpoints(spec.parse_documents(raw)) == (Endpoint("GET", "/a", "getA", response_shape="array"),)


def test_parse_embedded_literals_merges_each_document() -> None:
    """A page bundle's ``JSON.parse('…')`` literals are each a document; a later repeat of an operation wins."""
    first = json.dumps({"openapi": "3", "paths": {"/a": {"get": {"operationId": "old"}}}})
    second = json.dumps({"openapi": "3", "paths": {"/a": {"get": {"operationId": "new"}}, "/b": {"put": {}}}})
    other = json.dumps({"not": "a spec"})
    bundle = f"var x=JSON.parse('{first}'),y=JSON.parse('{other}');var z=JSON.parse('{second.replace("'", "\\'")}')"
    assert spec.endpoints(spec.parse_documents(bundle)) == (Endpoint("GET", "/a", "new"), Endpoint("PUT", "/b"))


@pytest.mark.parametrize("raw", ["just text", "[1, 2]", '{"openapi": "3"}', "var x = JSON.parse('{}');"])
def test_parse_rejects_a_source_with_no_document(raw: str) -> None:
    """A source with no object holding a ``paths`` table is a ``SpecError``."""
    with pytest.raises(spec.SpecError, match="no OpenAPI or Swagger document"):
        spec.parse_documents(raw)


def test_swagger_two_body_parameter_and_response_schema() -> None:
    """A Swagger 2 ``in: body`` parameter names the request schema; ``schema`` on the response names the answer."""
    operation = {
        "parameters": [{"in": "query", "name": "q"}, {"in": "body", "schema": {"$ref": "#/definitions/Pet"}}],
        "responses": {"201": {"schema": {"$ref": "#/definitions/Pet"}}},
    }
    document = {"definitions": {"Pet": {"type": "object"}}}
    assert spec.request_schema(operation) == "Pet"
    assert spec.response_shape(operation, document) == "object"


@pytest.mark.parametrize(
    "operation",
    [
        {},
        {"responses": []},
        {"responses": {"200": {"content": {}}}},
        {"responses": {"200": {"content": {"application/json": "text"}}}},
        {"responses": {"200": {"content": {"application/json": {"schema": {"$ref": "#/nowhere/at/all"}}}}}},
        {"parameters": "not a list"},
    ],
)
def test_details_are_empty_when_the_spec_is_silent(operation: dict[str, object]) -> None:
    """An operation with no readable success schema or body gives ``""`` for each."""
    assert spec.response_shape(operation, {"nowhere": "text"}) == ""
    assert spec.request_schema(operation) == ""


def test_a_ref_loop_stops() -> None:
    """A ``$ref`` that points at itself is followed a bounded number of times, then reads as no schema."""
    document = {"components": {"schemas": {"A": {"$ref": "#/components/schemas/A"}}}}
    operation = {"responses": {"200": {"schema": {"$ref": "#/components/schemas/A"}}}}
    assert spec.response_shape(operation, document) == ""


# the snapshot file


def test_dump_round_trips(tmp_path: Path) -> None:
    """``dump_snapshot`` writes what ``load_snapshot`` reads back unchanged."""
    snapshot = DocsSnapshot("https://x.example/openapi.json", date(2026, 10, 28), "why", _EXPECTED)
    path = tmp_path / "docs_paths.json"
    path.write_text(dump_snapshot(snapshot), encoding="utf-8")
    assert load_snapshot(path) == snapshot


@pytest.mark.parametrize(
    ("endpoint", "fragment"),
    [
        ({"verb": "GET", "path": "/a", "operation_id": 1}, "operation_id must be a string"),
        ({"verb": "GET", "path": "/a", "response_shape": "list"}, "array, object or empty"),
        ({"verb": "GET", "path": "/a", "tags": []}, "only operation_id"),
    ],
)
def test_load_rejects_bad_details(tmp_path: Path, endpoint: dict[str, object], fragment: str) -> None:
    """An operation detail that is not a string, an unknown shape, or an unknown key is a ``SnapshotError``."""
    path = tmp_path / "docs_paths.json"
    data = {"source": "https://x.example/", "retrieved": "2026-10-28", "reason": None, "endpoints": [endpoint]}
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(SnapshotError, match=fragment):
        load_snapshot(path)


# reading a source


class _Response:
    def __init__(self, status: int, body: bytes, headers: dict[str, str]) -> None:
        self.status = status
        self.reason = "Reason"
        self._body = body
        self._headers = headers
        self.msg = self

    def read(self) -> bytes:
        return self._body

    def getheader(self, name: str) -> str | None:
        return self._headers.get(name)

    def get_content_charset(self) -> str | None:
        content_type = self._headers.get("Content-Type", "")
        return content_type.partition("charset=")[2] or None


class _Server:
    """Stands in for ``http.client.HTTPSConnection``: answers each ``(host, target)`` from a table, and records."""

    def __init__(self, answers: dict[tuple[str, str], _Response]) -> None:
        self.answers = answers
        self.requests: list[tuple[str, str, dict[str, str]]] = []

    def __call__(self, host: str, *, timeout: int) -> _Connection:
        assert timeout > 0
        return _Connection(self, host)


class _Connection:
    def __init__(self, server: _Server, host: str) -> None:
        self.server = server
        self.host = host
        self.target = ""

    def request(self, method: str, target: str, *, headers: dict[str, str]) -> None:
        assert method == "GET"
        self.target = target
        self.server.requests.append((self.host, target, headers))

    def getresponse(self) -> _Response:
        return self.server.answers[self.host, self.target]

    def close(self) -> None:
        self.target = ""


def _serve(monkeypatch: pytest.MonkeyPatch, answers: dict[tuple[str, str], _Response]) -> _Server:
    server = _Server(answers)
    monkeypatch.setattr(spec.http.client, "HTTPSConnection", server)
    return server


def test_fetch_follows_a_redirect_and_dates_by_the_server(monkeypatch: pytest.MonkeyPatch) -> None:
    """A redirect is followed, the request names this tool, and ``retrieved`` is the ``Date`` header's day in UTC."""
    server = _serve(
        monkeypatch,
        {
            ("docs.example", "/openapi?v=1"): _Response(302, b"", {"Location": "https://cdn.example/spec.json"}),
            ("cdn.example", "/spec.json"): _Response(
                200,
                json.dumps(_OPENAPI).encode("latin-1"),
                {"Date": "Wed, 28 Oct 2026 23:30:00 -0700", "Content-Type": "application/json; charset=latin-1"},
            ),
        },
    )
    snapshot = spec.snapshot_of("https://docs.example/openapi?v=1")
    assert snapshot.retrieved == date(2026, 10, 29)
    assert snapshot.endpoints == _EXPECTED
    headers = server.requests[0][2]
    assert headers["User-Agent"].startswith("headgate-snapshot/")
    assert headers["Accept"].startswith("application/vnd.oai.openapi+json")


def test_fetch_without_a_date_uses_today(monkeypatch: pytest.MonkeyPatch) -> None:
    """A response with no ``Date`` header is dated today, in UTC."""
    _serve(monkeypatch, {("x.example", "/"): _Response(200, json.dumps(_OPENAPI).encode(), {})})
    assert spec.read_source("https://x.example")[1] == datetime.now(UTC).date()


@pytest.mark.parametrize(
    ("answers", "fragment"),
    [
        ({("x.example", "/s"): _Response(403, b"", {})}, "answered 403"),
        ({("x.example", "/s"): _Response(301, b"", {"Location": "http://x.example/s"})}, "not an https URL"),
        ({("x.example", "/s"): _Response(301, b"", {"Location": "/s"})}, "redirected more than 5 times"),
        ({("x.example", "/s"): _Response(200, b"\xff", {})}, "cannot be read"),
    ],
)
def test_fetch_failures(
    monkeypatch: pytest.MonkeyPatch, answers: dict[tuple[str, str], _Response], fragment: str
) -> None:
    """A refusal, a downgrade to http, a redirect loop and a body that is not text are each a ``SpecError``."""
    _serve(monkeypatch, answers)
    with pytest.raises(spec.SpecError, match=fragment):
        spec.read_source("https://x.example/s")


def test_a_missing_file_is_a_spec_error(tmp_path: Path) -> None:
    """A local source that cannot be read is a ``SpecError`` naming it."""
    with pytest.raises(spec.SpecError, match="cannot be read"):
        spec.read_source(str(tmp_path / "missing.json"))


# write, refresh and the command


def test_write_then_refresh_keeps_the_reason(tmp_path: Path) -> None:
    """``write`` keeps the ``reason`` a snapshot already has; ``refresh`` reads ``source`` again."""
    source = tmp_path / "openapi.json"
    source.write_text(json.dumps(_OPENAPI), encoding="utf-8")
    target = tmp_path / "docs_paths.json"
    assert spec.write(target, str(source)).reason is None
    data = json.loads(target.read_text(encoding="utf-8"))
    target.write_text(json.dumps(data | {"reason": "two documents", "endpoints": []}), encoding="utf-8")
    refreshed = spec.refresh(target)
    assert refreshed.reason == "two documents"
    assert refreshed.endpoints == _EXPECTED
    assert spec.write(target, str(source)).reason == "two documents"


def test_refresh_needs_a_source(tmp_path: Path) -> None:
    """A snapshot with source null has nothing to read again."""
    target = tmp_path / "docs_paths.json"
    data = {"source": None, "retrieved": "2026-10-28", "reason": "no spec", "endpoints": []}
    target.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(spec.SpecError, match="source null"):
        spec.refresh(target)


def test_main_write_and_refresh(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """``write`` and ``refresh`` each report the file they wrote and exit 0."""
    source = tmp_path / "openapi.yaml"
    source.write_text(json.dumps(_OPENAPI), encoding="utf-8")
    target = tmp_path / "docs_paths.json"
    assert spec.main(["write", str(target), str(source)]) == 0
    assert spec.main(["refresh", str(target)]) == 0
    assert capsys.readouterr().err.splitlines() == [f"wrote {target}: 4 endpoints from {source}"] * 2


def test_main_reports_each_failure(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A target that cannot be written says why on stderr, and the run exits 2."""
    source = tmp_path / "broken.json"
    source.write_text("{", encoding="utf-8")
    assert spec.main(["write", str(tmp_path / "docs_paths.json"), str(source)]) == USAGE_ERROR
    assert spec.main(["refresh", str(tmp_path / "missing.json")]) == USAGE_ERROR
    first, second = capsys.readouterr().err.splitlines()
    assert first.startswith(f"headgate-snapshot: {tmp_path / 'docs_paths.json'}: ")
    assert second.startswith(f"headgate-snapshot: {tmp_path / 'missing.json'}: the file cannot be read")


@pytest.mark.parametrize(("argv", "code"), [(["--help"], 0), (["write"], 2), ([], 2)])
def test_main_usage(argv: list[str], code: int) -> None:
    """``--help`` exits 0 and a usage error exits 2, never raising ``SystemExit``."""
    assert spec.main(argv) == code
