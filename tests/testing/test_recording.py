# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Tests for the recording helpers: the scrubs, the composed vcrpy hooks, ``drive``, and a real record and replay."""

import base64
import json
import subprocess
import sys
from typing import TYPE_CHECKING, override
from urllib.parse import quote

import httpx2
import msgspec
import pytest
import yaml
from headgate.testing import CassetteFilter, FakeTransport, TestClock, isolated_breakers
from vcr.request import Request

from examples.msgspec.lda.client import LdaClient
from headgate_verify.testing import creds
from headgate_verify.testing.manifest import Endpoint
from headgate_verify.testing.recording import REDACTED, TOKEN_KEYS, Recording, drive, recorded, redact_by_key, scrub

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path

SECRET = "sk-live-ABCDEF-1234567890"  # noqa: S105 -- a made-up key the scrub must remove


def _response(body: bytes | str, headers: dict[str, list[str]] | None = None) -> dict[str, object]:
    return {"status": {"code": 200, "message": "OK"}, "headers": headers or {}, "body": {"string": body}}


# --- scrub ----------------------------------------------------------------------


def test_scrub_replaces_every_spelling_of_a_secret() -> None:
    """Scrub replaces every spelling of a secret."""
    spellings = [SECRET, quote(SECRET, safe=""), base64.b64encode(SECRET.encode()).decode(), json.dumps(SECRET)[1:-1]]
    text = " ".join(spellings)
    assert scrub(text, [SECRET]) == " ".join([REDACTED] * len(spellings))


def test_scrub_replaces_the_longer_of_two_prefixed_secrets_first() -> None:
    """Replacing the prefix first would leave the longer secret's tail, still key material, behind."""
    assert scrub(f"{SECRET}!", ["sk-live-ABCDEF", SECRET]) == f"{REDACTED}!"


def test_scrub_leaves_a_value_too_short_to_be_a_key() -> None:
    """Scrub leaves a value too short to be a key."""
    assert scrub("id=12345", ["12345"]) == "id=12345"


def test_scrub_catches_a_lowercased_percent_encoding() -> None:
    """Scrub catches a lowercased percent encoding."""
    secret = "a/b+c=d/e"  # noqa: S105 -- a made-up key
    assert scrub(quote(secret, safe="").lower(), [secret]) == REDACTED


# --- redact_by_key --------------------------------------------------------------


def test_redact_by_key_reaches_every_depth_and_keeps_empties_and_booleans() -> None:
    """Redact by key reaches every depth and keeps empties and booleans."""
    body = {"data": [{"access_token": "t-1", "refresh_token": "", "id_token": True, "n": 1}], "accessToken": 7}
    assert redact_by_key(body) == {
        "data": [{"access_token": REDACTED, "refresh_token": "", "id_token": True, "n": 1}],
        "accessToken": REDACTED,
    }


def test_redact_by_key_takes_a_package_s_own_keys() -> None:
    """Redact by key takes a package's own keys."""
    body = {"account_number": "PA123", "access_token": "t"}
    assert redact_by_key(body, TOKEN_KEYS | {"account_number"}) == {
        "account_number": REDACTED,
        "access_token": REDACTED,
    }
    assert redact_by_key(body, frozenset()) == body


# --- Recording's hooks ----------------------------------------------------------


@pytest.fixture
def handed_out_secret() -> None:
    """Hand ``SECRET`` out through the credentials provider, as a live client's constructor would ask for it."""
    previous = creds.use(lambda _provider, _name: SECRET)
    try:
        creds.require("demo", "key")
    finally:
        creds.use(previous)


@pytest.mark.usefixtures("handed_out_secret")
def test_a_request_keeps_only_content_type_and_loses_every_secret() -> None:
    """A request keeps only content type and loses every secret."""
    recording = Recording(placeholders={("demo", "key"): "replay-demo-key"}, also_redact=frozenset({"acct-998877"}))
    request = Request(
        "POST",
        f"https://api.example.test/v1/acct-998877/orders?key={SECRET}&replay=replay-demo-key",
        f'{{"key": "{SECRET}"}}'.encode(),
        {"Authorization": f"Bearer {SECRET}", "Content-Type": "application/json", "User-Agent": "ops"},
    )
    scrubbed = recording.before_record_request(request)
    assert scrubbed.uri == f"https://api.example.test/v1/{REDACTED}/orders?key={REDACTED}&replay={REDACTED}"
    assert scrubbed.body == f'{{"key": "{REDACTED}"}}'.encode()
    assert dict(scrubbed.headers) == {"Content-Type": "application/json"}


@pytest.mark.usefixtures("handed_out_secret")
def test_a_json_response_is_redacted_scrubbed_and_pretty_printed() -> None:
    """A json response is redacted scrubbed and pretty printed."""
    recording = Recording(scrub_body=lambda body: {**body, "balance": "0"} if isinstance(body, dict) else body)
    body = json.dumps({"echo": SECRET, "access_token": "minted-xyz", "balance": "1234.56"}).encode()
    headers = {"Content-Type": ["application/json"], "Set-Cookie": ["s=1"], "CF-Ray": ["abc"]}
    response = recording.before_record_response(_response(body, headers))
    assert response["headers"] == {"Content-Type": ["application/json"]}
    assert json.loads(response["body"]["string"]) == {"access_token": REDACTED, "balance": "0", "echo": REDACTED}
    assert response["body"]["string"].startswith(b'{\n  "access_token"')


@pytest.mark.usefixtures("handed_out_secret")
def test_a_text_response_is_scrubbed_and_a_binary_one_kept_byte_for_byte() -> None:
    """A text response is scrubbed and a binary one kept byte for byte."""
    recording = Recording()
    text = recording.before_record_response(_response(f"key={SECRET}"))
    assert text["body"]["string"] == f"key={REDACTED}".encode()
    binary = b"PK\x03\x04\xff\xfe" + SECRET.encode()
    assert recording.before_record_response(_response(binary))["body"]["string"] == binary
    assert recording.before_record_response(_response({"not": "a body"}))["body"]["string"] == {"not": "a body"}  # ty: ignore[invalid-argument-type]  # vcrpy's body may be anything


def test_a_request_with_a_binary_body_keeps_it() -> None:
    """A request with a binary body keeps it."""
    request = Request("PUT", "https://api.example.test/upload", b"\xff\xfe\x00", {})
    assert Recording().before_record_request(request).body == b"\xff\xfe\x00"


def test_headgate_s_cassette_filter_runs_first_and_its_query_filter_joins() -> None:
    """A token mint the filter drops is not recorded at all, and its ``Set-Cookie`` drop still holds."""
    recording = Recording(
        cassette_filter=CassetteFilter(params=("api_key",)), keep_headers=frozenset({"Content-Type", "Set-Cookie"})
    )
    config = recording.vcr_config()
    assert config["filter_query_parameters"] == ["api_key"]
    assert config["decode_compressed_response"] is True
    response = recording.before_record_response(
        _response("ok", {"Set-Cookie": ["s=1"], "content-type": ["text/plain"]})
    )
    assert response["headers"] == {"content-type": ["text/plain"]}
    request = Request("GET", "https://user:pw@api.example.test/v1", None, {})
    assert recording.before_record_request(request).uri == "https://***@api.example.test/v1"


def test_a_mint_the_cassette_filter_skips_is_not_recorded() -> None:
    """A mint the cassette filter skips is not recorded."""

    class Skips(CassetteFilter):
        @override
        def before_record_request(self, request: object) -> None:
            """Skip every request, as the filter does a token mint."""
            del request

    assert Recording(cassette_filter=Skips()).before_record_request(Request("GET", "https://a.test/", None, {})) is None


def test_the_vcr_config_without_a_filter_names_only_the_hooks() -> None:
    """The vcr config without a filter names only the hooks."""
    recording = Recording()
    assert set(recording.vcr_config()) == {
        "decode_compressed_response",
        "before_record_request",
        "before_record_response",
    }
    assert recording.replay_lookup("demo", "key") is None


# --- drive and recorded ---------------------------------------------------------


class _Constant(msgspec.Struct):
    name: str


PAGE = {"count": 3, "next": "https://lda.gov/api/v1/filings/?page=2", "previous": None, "results": []}


@pytest.fixture
async def lda() -> AsyncIterator[tuple[LdaClient, FakeTransport]]:
    """Yield the lda client on a fake network, with its clock and breakers isolated."""
    fake = FakeTransport()
    with TestClock().install(), isolated_breakers():
        yield LdaClient(user_agent="ua-test", transport=fake), fake


@pytest.mark.anyio
async def test_drive_reads_one_page_of_a_walk_and_closes_the_client(lda: tuple[LdaClient, FakeTransport]) -> None:
    """Drive reads one page of a walk and closes the client."""
    client, fake = lda
    fake.reply("GET", "/api/v1/filings/", httpx2.Response(200, json=PAGE))
    await drive(
        client,
        Endpoint(method="get_filings", kwargs={"filing_year": 2025}, path="/filings/", envelope=object, paginated=True),
    )
    assert len(fake.calls) == 1
    assert client._http_client.is_closed  # noqa: SLF001 -- whether drive closed the client


@pytest.mark.anyio
async def test_drive_awaits_a_single_read(lda: tuple[LdaClient, FakeTransport]) -> None:
    """Drive awaits a single read."""
    client, fake = lda
    fake.reply("GET", "/api/v1/constants/general/countries/", httpx2.Response(200, json=[]))
    await drive(
        client,
        Endpoint(
            method="get_constants_general_countries", path="/constants/general/countries/", envelope=list[_Constant]
        ),
    )
    assert len(fake.calls) == 1


@pytest.mark.anyio
async def test_drive_reads_a_stream_directly_and_closes_it() -> None:
    """Drive reads a stream directly and closes it."""
    closed: list[bool] = []

    class Streaming:
        async def stream_rows(self) -> AsyncIterator[int]:
            try:
                yield 1
                yield 2
            finally:
                closed.append(True)

        async def aclose(self) -> None:
            closed.append(False)

    await drive(Streaming(), Endpoint(method="stream_rows", path="/rows", envelope=int, paginated=True))  # ty: ignore[invalid-argument-type]  # a duck client
    assert closed == [True, False]


def test_recorded_skips_an_endpoint_not_to_capture_and_ids_by_method() -> None:
    """Recorded skips an endpoint not to capture and ids by method."""
    safe = Endpoint(method="get_orders", path="/orders", envelope=object)
    unsafe = Endpoint(method="cancel_order", path="/orders/{id}", envelope=type(None), capture=False)
    params = recorded([safe, unsafe])
    assert [param.id for param in params] == ["get_orders"]
    assert params[0].values == (safe,)


# --- a real record, then a replay ------------------------------------------------

_CONFTEST = """
import pytest
from headgate_verify.testing.recording import Recording

pytest_plugins = ["headgate_verify.testing.plugin"]
RECORDING = Recording(placeholders={("demo", "key"): "replay-demo-key"})


@pytest.fixture(scope="module")
def vcr_config():
    return RECORDING.vcr_config()


@pytest.fixture
def recording():
    return RECORDING
"""

_TEST = """
import httpx2
import pytest
from headgate_verify.testing import creds
from headgate_verify.testing.recording import no_retry_backoff, replay_credentials  # noqa: F401


def serve(request):
    if request.url.params["key"] != "sk-live-ABCDEF-1234567890":
        raise AssertionError("the replay reached the network")
    body = {"echo": request.url.params["key"], "access_token": "minted-token-1", "rows": [1, 2]}
    return httpx2.Response(200, json=body, headers={"Set-Cookie": "session=abc", "X-Request-Id": "r-1"})


@pytest.mark.vcr
def test_endpoint():
    key = creds.require("demo", "key")["key"]
    with httpx2.Client(transport=httpx2.MockTransport(serve)) as client:
        response = client.get("https://api.example.test/v1/rows", params={"key": key})
    assert response.json()["rows"] == [1, 2]
"""


def test_a_recording_holds_no_secret_and_replays_with_no_credential(tmp_path: Path) -> None:
    """Record through vcrpy's httpx2 patch with the live key, then replay under the placeholder with no provider."""
    (tmp_path / "conftest.py").write_text(_CONFTEST, encoding="utf-8")
    (tmp_path / "test_rows.py").write_text(_TEST, encoding="utf-8")
    (tmp_path / "ops_secrets.py").write_text(f"def lookup(provider, name):\n    return {SECRET!r}\n", encoding="utf-8")

    def run(*args: str) -> str:
        command = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", *args]
        done = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, check=False)  # noqa: S603 -- this interpreter, over files the test wrote
        return done.stdout + done.stderr

    assert "1 passed" in run("--record-mode=once", "--credentials-provider", "ops_secrets:lookup")
    cassette = tmp_path / "cassettes" / "test_rows" / "test_endpoint.yaml"
    text = cassette.read_text(encoding="utf-8")
    assert SECRET not in text
    assert "minted-token-1" not in text
    assert "session=abc" not in text
    interaction = yaml.safe_load(text)["interactions"][0]
    assert interaction["request"]["uri"] == f"https://api.example.test/v1/rows?key={REDACTED}"
    assert set(interaction["response"]["headers"]) == {"content-type"}

    assert "1 passed" in run()
