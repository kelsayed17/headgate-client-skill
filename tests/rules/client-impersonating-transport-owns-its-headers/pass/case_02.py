class AsyncCurlTransport(httpx2.AsyncBaseTransport):
    def __init__(self, *, impersonate: str, default_headers: bool = False) -> None:
        self._session = AsyncSession(impersonate=impersonate, default_headers=default_headers)


factory = AsyncCurlTransport
available = AsyncCurlTransport.supported(impersonate="chrome")
plain = httpx2.AsyncHTTPTransport(retries=0)
other = AsyncCurlTransportFactory(impersonate="chrome")
