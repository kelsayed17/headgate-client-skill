# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Tests for the leaf mock: it replaces only the network leaf, so headgate's retry and pacing still run above it."""

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import httpx2
import pytest
from headgate import UpstreamStatusError
from headgate.testing import TestClock, isolated_breakers

from examples.msgspec.lda.client import LdaClient
from headgate_verify.testing.leaf_mock import MockHTTP, install

if TYPE_CHECKING:
    from headgate import AsyncBaseClient

pytestmark = pytest.mark.anyio

FILING = b'{"filing_uuid": "u", "url": "https://lda.gov/api/v1/filings/u/"}'


def _json(status: int, body: bytes = b"{}") -> httpx2.Response:
    return httpx2.Response(status, content=body, headers={"Content-Type": "application/json"})


async def test_install_replaces_the_leaf_below_the_retry_layer() -> None:
    """A 503 then a 200: the client's own retry, still in the stack, takes the second answer."""
    clock = TestClock()
    with clock.install(), isolated_breakers():
        client = LdaClient(user_agent="ua-test")
        mock = install(client, MockHTTP().sequence(_json(503), _json(404)))
        async with client:
            assert await client.get_filing("u") is None
    assert mock.call_count == 2  # noqa: PLR2004 -- the 503 and the retry
    assert mock.last.url.path == "/api/v1/filings/u/"


async def test_an_exception_entry_is_raised_and_the_last_entry_repeats() -> None:
    """An exception entry is raised and the last entry repeats."""
    mock = MockHTTP().sequence(httpx2.ConnectError("down"), _json(200))
    transport = mock.transport()
    request = httpx2.Request("GET", "https://example.test/")
    with pytest.raises(httpx2.ConnectError):
        await transport.handle_async_request(request)
    for _ in range(2):
        assert (await transport.handle_async_request(request)).status_code == 200  # noqa: PLR2004 -- the scripted status
    assert mock.call_count == 3  # noqa: PLR2004 -- the failure and two answers


async def test_returns_raises_and_handler_configure_every_request() -> None:
    """Returns raises and handler configure every request."""
    request = httpx2.Request("GET", "https://example.test/a")
    mock = MockHTTP()
    mock.response = _json(201)
    assert mock.response is None
    assert (await mock.transport().handle_async_request(request)).status_code == 201  # noqa: PLR2004 -- the scripted status
    mock.error = httpx2.ReadTimeout("slow")
    assert mock.error is None
    with pytest.raises(httpx2.ReadTimeout):
        await mock.transport().handle_async_request(request)
    mock.handler(lambda req: _json(200, req.url.path.encode()))
    assert (await mock.transport().handle_async_request(request)).content == b"/a"


async def test_an_unconfigured_mock_fails_the_test() -> None:
    """An unconfigured mock fails the test."""
    with pytest.raises(AssertionError, match="before being configured"):
        await MockHTTP().transport().handle_async_request(httpx2.Request("GET", "https://example.test/"))


async def test_a_client_whose_transport_has_no_child_is_replaced_whole() -> None:
    """A client whose transport has no child is replaced whole."""
    http_client = SimpleNamespace(_transport=httpx2.MockTransport(lambda _req: _json(500)))
    client = cast("AsyncBaseClient", SimpleNamespace(_http_client=http_client))
    install(client, MockHTTP().returns(_json(200)))
    response = await http_client._transport.handle_async_request(  # noqa: SLF001 -- the stub's own leaf
        httpx2.Request("GET", "https://example.test/")
    )
    assert response.status_code == 200  # noqa: PLR2004 -- the scripted status


async def test_a_status_the_client_maps_still_raises_through_the_mock() -> None:
    """A status the client maps still raises through the mock."""
    with TestClock().install(), isolated_breakers():
        client = LdaClient(user_agent="ua-test")
        install(client, MockHTTP().returns(_json(400, b'{"detail": "bad year"}')))
        async with client:
            with pytest.raises(UpstreamStatusError):
                await client.get_contribution("u")
