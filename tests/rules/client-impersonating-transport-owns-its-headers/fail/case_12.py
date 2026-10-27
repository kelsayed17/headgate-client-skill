def _chrome_transport() -> httpx2.AsyncBaseTransport:
    return AsyncCurlTransport(impersonate="chrome")
