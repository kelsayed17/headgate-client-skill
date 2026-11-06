# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""A scripted transport spliced at a client's network LEAF, for a client no ``transport=`` argument reaches.

A client that takes ``transport=`` is tested with :class:`headgate.testing.FakeTransport` passed in, which is the
pattern ``references/testing.md`` describes. This module is the exception, for a client that builds its own leaf: a
curl transport (``headgate.curl.AsyncCurlTransport``, for TLS impersonation) sends its requests itself, so neither a
fake passed in nor a library patching httpx2's transport class reaches it, and a test would reach the real network.
:func:`install` walks the client's built stack and replaces whatever its leaf is with a :class:`MockHTTP`, below every
policy layer (retry, cache, rate limit), so those still run for real.

It reads headgate's private stack attributes (``_http_client`` and each layer's child), so it may need updating with
headgate; prefer ``transport=`` wherever a client accepts it.
"""

from typing import TYPE_CHECKING

import httpx2

if TYPE_CHECKING:
    from collections.abc import Callable

    from headgate import AsyncBaseClient

__all__ = ["MockHTTP", "install"]


class MockHTTP:
    """Records requests and serves scripted responses at the transport layer."""

    def __init__(self) -> None:
        """Start unconfigured, with no request seen; a request before configuration fails the test."""
        self.requests: list[httpx2.Request] = []
        self._handler: Callable[[httpx2.Request], httpx2.Response] | None = None

    # -- configuration -------------------------------------------------

    def returns(self, response: httpx2.Response) -> MockHTTP:
        """Serve *response* for every request."""
        self._handler = lambda _req: response
        return self

    def sequence(self, *responses: httpx2.Response | BaseException) -> MockHTTP:
        """Serve each entry in order; the last one repeats once exhausted.

        An exception entry is raised instead of returned — the shape retry
        and circuit-breaker tests need (fail, fail, then succeed).
        """
        queue = list(responses)

        def handler(_req: httpx2.Request) -> httpx2.Response:
            item = queue.pop(0) if len(queue) > 1 else queue[0]
            if isinstance(item, BaseException):
                raise item
            return item

        self._handler = handler
        return self

    def raises(self, exc: BaseException) -> MockHTTP:
        """Raise *exc* for every request (network failure simulation)."""

        def handler(_req: httpx2.Request) -> httpx2.Response:
            raise exc

        self._handler = handler
        return self

    def handler(self, fn: Callable[[httpx2.Request], httpx2.Response]) -> MockHTTP:
        """Serve responses from an arbitrary per-request callable."""
        self._handler = fn
        return self

    # Assignment-style aliases: ``mock.response = ...`` reads like a ``unittest.mock`` return value.

    @property
    def response(self) -> httpx2.Response | None:
        """Write-mostly: assign the response every request should get."""
        return None

    @response.setter
    def response(self, resp: httpx2.Response) -> None:
        self.returns(resp)

    @property
    def error(self) -> BaseException | None:
        """Write-mostly: assign the exception every request should raise."""
        return None

    @error.setter
    def error(self, exc: BaseException) -> None:
        self.raises(exc)

    # -- assertions ----------------------------------------------------

    @property
    def call_count(self) -> int:
        """How many requests reached the mock."""
        return len(self.requests)

    @property
    def last(self) -> httpx2.Request:
        """The most recent request."""
        return self.requests[-1]

    # -- wiring --------------------------------------------------------

    def transport(self) -> httpx2.MockTransport:
        """Return an httpx2 transport that records each request and answers it as configured."""

        def handle(request: httpx2.Request) -> httpx2.Response:
            self.requests.append(request)
            if self._handler is None:
                msg = "MockHTTP received a request before being configured"
                raise AssertionError(msg)
            return self._handler(request)

        return httpx2.MockTransport(handle)


#: The attribute each of headgate's stack layers holds its child under: ``_transport`` for most of them, ``_inner``
#: and hishel's ``next_transport`` inside the cache layer.
_CHILD_ATTRS = ("_transport", "_inner", "next_transport")


def install(client: AsyncBaseClient, mock: MockHTTP) -> MockHTTP:
    """Swap *client*'s innermost network transport for *mock*.

    Descends headgate's whole stack — ``RetryTransport(…((cache)(RateLimitTransport(…(network)))))`` — and
    replaces only the leaf, so every policy layer
    above it keeps running for real. It walks by attribute rather than by a known depth
    because the stack's shape is per client (the cache layer is opt-in), and because a
    layer added below the splice point would otherwise be silently cut out of every test
    that uses this helper.

    Falls back to replacing the client's whole transport if nothing below it is an
    ``AsyncBaseTransport`` (a client constructed with a custom ``transport=`` that
    exposes no child).
    """
    parent: object = client._http_client  # noqa: SLF001 -- headgate exposes no accessor for the stack it built
    attr = "_transport"
    node: httpx2.AsyncBaseTransport = client._http_client._transport  # noqa: SLF001 -- as above
    while True:
        for name in _CHILD_ATTRS:
            child = getattr(node, name, None)
            if isinstance(child, httpx2.AsyncBaseTransport):
                parent, attr, node = node, name, child
                break
        else:
            break
    setattr(parent, attr, mock.transport())
    return mock
