# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Record a client's live wire as vcrpy cassettes, scrubbed, and replay it offline: one capture path for any client.

A package records by marking a test ``vcr`` (pytest-recording) and driving its client through the real transport
stack; ``pytest --record-mode=rewrite`` writes ``cassettes/<module>/<test>.yaml``, and every other run replays it,
failing on any request the cassette lacks. vcrpy patches httpx2's own transports, below headgate's whole stack, so
retries, the cache and the rate limit run over a replay as they do over the network. A client built on another leaf
(curl) is neither recorded nor replayed.

The package's ``conftest.py`` builds one :class:`Recording`, hands pytest-recording its :meth:`Recording.vcr_config`,
and exposes it as a ``recording`` fixture; its recorded test module imports :func:`replay_credentials` and
:func:`no_retry_backoff` so they apply there::

    RECORDING = Recording(placeholders={("lda", "api_key"): "replay-lda-api-key"})

    @pytest.fixture(scope="module")
    def vcr_config() -> dict[str, object]:
        return RECORDING.vcr_config()

    @pytest.fixture
    def recording() -> Recording:
        return RECORDING

**What is scrubbed.** A cassette is committed, so everything a recording could carry that is not the provider's
public wire is removed before it is written:

* every credential and contact the clients were handed (:func:`headgate_verify.testing.creds.handed_out`) and every
  replay placeholder, in every spelling a body or URL can carry it (raw, percent-encoded either case, base64,
  JSON-escaped), longest first, from the request URI, the request body and the response body;
* every value under a JSON key in :attr:`Recording.redact_keys` (default :data:`TOKEN_KEYS`, the tokens a mint flow
  returns: the bearer it mints was never handed out, so no value scrub knows it). A provider that echoes an account
  number adds its keys (``redact_keys=TOKEN_KEYS | {"account_number"}``);
* every request and response header but those in :attr:`Recording.keep_headers` (``Content-Type``): auth headers, the
  User-Agent's contact, cookies and CDN ids are none of the wire's shape;
* whatever the package's :attr:`Recording.scrub_body` hook rewrites in each parsed JSON body.

Only values handed out are scrubbed, never a guess at what looks like a secret: over-scrubbing fabricates as surely as
under-recording leaks (a base URL scrubbed as a "secret" rewrites every ``next`` link, and nothing can tell a redacted
cursor from a real one).

**Replay needs no credential.** :func:`replay_credentials` answers every ``(provider, field)`` with its placeholder
when nothing is being recorded, so a client builds offline exactly as it does live; the placeholders are scrubbed
like the real values, which is what lets a replayed request match its recording.

**headgate's own filter composes.** Pass ``cassette_filter=CassetteFilter(auths=...)`` (:mod:`headgate.testing`) and
put the filter in the client's middleware: its hooks run first, so a token mint it drops stays out of the cassette,
and its query filter joins this one's.
"""

import asyncio
import base64
import json
from contextlib import nullcontext
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from urllib.parse import quote, quote_plus

import pytest
from headgate.testing import instant_retries

from headgate_verify.testing import creds

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping

    from headgate import AsyncBaseClient
    from headgate.testing import CassetteFilter

    from headgate_verify.testing.manifest import Endpoint

__all__ = [
    "REDACTED",
    "TOKEN_KEYS",
    "Recording",
    "drive",
    "no_retry_backoff",
    "recorded",
    "redact_by_key",
    "replay_credentials",
    "scrub",
]

#: What every scrubbed value becomes.
REDACTED = "<redacted>"

# Below this length a "secret" is more likely a common substring than a key, and redacting it would corrupt the body.
_MIN_SECRET_LEN = 6

# One endpoint's bound while recording: a walk that never ends is a failure to report, not a cassette to wait for.
_ENDPOINT_TIMEOUT = 120.0

#: JSON keys whose values are a minted TOKEN, redacted by NAME wherever they occur.
TOKEN_KEYS = frozenset(
    {
        "accessToken",
        "access_token",
        "refreshToken",
        "refresh_token",
        "idToken",
        "id_token",
    }
)


def _variants(secret: str) -> list[str]:
    """Each spelling *secret* can take in a URL or a body: raw, percent-encoded (either case), base64, JSON-escaped."""
    percent = {quote(secret, safe=""), quote_plus(secret)}
    forms = {secret, *percent, *(form.lower() for form in percent), json.dumps(secret)[1:-1]}
    forms.add(base64.b64encode(secret.encode()).decode())
    return [form for form in forms if form]


def scrub(text: str, secrets: Iterable[str]) -> str:
    """Replace every spelling of every secret in *text* with :data:`REDACTED`, LONGEST first.

    The order is the guarantee: replacing a secret that PREFIXES another first leaves the longer one's tail behind
    (``ABCDEF-1234567890`` became ``<redacted>67890``), and a key's tail is still key material. A secret shorter than
    six characters is left alone.
    """
    for secret in sorted({s for s in secrets if len(s) >= _MIN_SECRET_LEN}, key=lambda s: (-len(s), s)):
        for form in _variants(secret):
            text = text.replace(form, REDACTED)
    return text


def redact_by_key(node: object, keys: frozenset[str] = TOKEN_KEYS) -> object:
    """Return *node* with every non-empty string or number under one of *keys* replaced by :data:`REDACTED`."""
    if isinstance(node, dict):
        return {
            key: REDACTED
            if key in keys and isinstance(value, str | int) and not isinstance(value, bool) and value
            else redact_by_key(value, keys)
            for key, value in node.items()
        }
    if isinstance(node, list):
        return [redact_by_key(item, keys) for item in node]
    return node


def _text(raw: bytes | str) -> str | None:
    """*raw* as text, or ``None`` for a body that is not UTF-8 (a file), which is kept byte for byte."""
    if isinstance(raw, str):
        return raw
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


@dataclass(frozen=True, kw_only=True)
class Recording:
    """One package's recording settings: its replay placeholders and its own scrubs, beside the shared ones."""

    #: What a replayed client is built with, per ``(provider, field)``; each is scrubbed like a real credential.
    placeholders: Mapping[tuple[str, str], str] = field(default_factory=dict)
    #: JSON keys whose values are redacted by name, wherever they occur.
    redact_keys: frozenset[str] = TOKEN_KEYS
    #: Rewrites each parsed JSON response body (a provider's balances, wallet ids), after the key redaction.
    scrub_body: Callable[[object], object] | None = None
    #: Values to scrub beyond the credentials: a manifest's placeholder for a value it reads at import.
    also_redact: frozenset[str] = frozenset()
    #: The only headers a recorded request or response keeps, compared case-insensitively.
    keep_headers: frozenset[str] = frozenset({"content-type"})
    #: headgate's own cassette filter, whose hooks run first.
    cassette_filter: CassetteFilter | None = None

    def secrets(self) -> frozenset[str]:
        """Every value a cassette must never hold: what the clients were handed, the placeholders, ``also_redact``."""
        return creds.handed_out() | frozenset(self.placeholders.values()) | self.also_redact

    def replay_lookup(self, provider: str, name: str) -> str | None:
        """Answer as the credentials provider a replay runs under: each placeholder, or ``None``."""
        return self.placeholders.get((provider, name))

    def vcr_config(self) -> dict[str, object]:
        """pytest-recording's settings: the scrubs above, with bodies stored decoded (``decode_compressed_response``).

        Each JSON response body is stored pretty-printed and key-sorted, so a re-recording diffs by field rather than
        as one changed line.
        """
        config: dict[str, object] = {
            "decode_compressed_response": True,
            "before_record_request": self.before_record_request,
            "before_record_response": self.before_record_response,
        }
        if self.cassette_filter is not None:
            config["filter_query_parameters"] = list(self.cassette_filter.filter_query_parameters)
        return config

    def _headers(self, headers: Mapping[str, Any]) -> dict[str, Any]:
        keep = {name.lower() for name in self.keep_headers}
        return {name: value for name, value in headers.items() if name.lower() in keep}

    def before_record_request(self, request: Any) -> Any:  # noqa: ANN401 -- vcrpy's Request is untyped
        """Scrub the URI and body and drop all but the kept headers: vcrpy applies it to a live and a replayed request.

        Returns ``None`` (vcrpy's "do not record") when the cassette filter skips the request, a token mint.
        """
        if self.cassette_filter is not None:
            request = self.cassette_filter.before_record_request(request)
            if request is None:
                return None
        secrets = self.secrets()
        request.uri = scrub(request.uri, secrets)
        if isinstance(request.body, bytes) and (text := _text(request.body)) is not None:
            request.body = scrub(text, secrets).encode()
        request.headers = self._headers(dict(request.headers))
        return request

    def before_record_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """Drop all but the kept headers, redact by key, apply ``scrub_body``, and scrub every secret from the body."""
        if self.cassette_filter is not None:
            response = dict(self.cassette_filter.before_record_response(response))
        response["headers"] = self._headers(response.get("headers") or {})
        raw = response["body"]["string"]
        if not isinstance(raw, bytes | str) or (text := _text(raw)) is None:
            return response
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            response["body"]["string"] = scrub(text, self.secrets()).encode()
            return response
        parsed = redact_by_key(parsed, self.redact_keys)
        if self.scrub_body is not None:
            parsed = self.scrub_body(parsed)
        formatted = json.dumps(parsed, indent=2, sort_keys=True, ensure_ascii=False)
        response["body"]["string"] = scrub(formatted, self.secrets()).encode()
        return response


@pytest.fixture(autouse=True)
def replay_credentials(record_mode: str, recording: Recording) -> Iterator[None]:
    """Answer every credential with its placeholder unless recording; recording keeps the operator's provider.

    Needs pytest-recording's ``record_mode`` and the package's ``recording`` fixture.
    """
    if record_mode != "none":
        yield
        return
    previous = creds.use(recording.replay_lookup)
    try:
        yield
    finally:
        creds.use(previous)


@pytest.fixture(autouse=True)
def no_retry_backoff(record_mode: str) -> Iterator[None]:
    """Instant retries and pacing on replay; the client's REAL pacing while recording live.

    Pacing a live recording instantly would spend the provider's rate budget in a burst and record its 429s.
    """
    with nullcontext() if record_mode != "none" else instant_retries():
        yield


async def drive(client: AsyncBaseClient, endpoint: Endpoint, *, limit: float = _ENDPOINT_TIMEOUT) -> None:
    """Call *endpoint* on *client*, consuming ONE page when it is paginated, then close the client.

    One page is the cassette: its first request is the one being recorded, and a walk past it would record (and on
    replay demand) every later page. A headgate ``Paginated`` is read through ``pages()``; any other async iterator
    (a stream) is read directly. An empty first page does not raise. A call that takes longer than *limit* seconds
    raises ``TimeoutError``: a walk that never ends is a failure to report, not a cassette to wait for.
    """
    try:
        async with asyncio.timeout(limit):
            call = getattr(client, endpoint.method)(*endpoint.args, **endpoint.kwargs)
            if not endpoint.paginated:
                await call
                return
            pages = call.pages() if hasattr(call, "pages") else call
            try:
                await anext(aiter(pages), None)
            finally:
                if (aclose := getattr(pages, "aclose", None)) is not None:
                    await aclose()
    finally:
        await client.aclose()


def recorded(endpoints: Iterable[Endpoint]) -> list[Any]:
    """Return the ``capture=True`` entries as pytest params, each id'd by its method: one cassette per endpoint.

    Parametrize a test named ``test_endpoint`` with it, and each cassette is ``test_endpoint[<method>].yaml``, the
    name :func:`headgate_verify.testing.cassettes.recorded_bodies` reads.
    """
    return [pytest.param(endpoint, id=endpoint.method) for endpoint in endpoints if endpoint.capture]
