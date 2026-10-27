class AsyncCurlTransport(httpx2.AsyncBaseTransport):
    """Mozilla/5.0 is what curl sends."""

    HEADERS = {"User-Agent": "x"}
