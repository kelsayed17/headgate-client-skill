class DualClient(AsyncBaseClient):
    def __init__(self, *, fast: bool = False, asgi_app: AsgiApp | None = None) -> None:
        super().__init__(
            base_url=_BASE_URL,
            rate=Rate.per_second(_FAST_PER_SEC if fast else _SLOW_PER_SEC),
            http=HttpOptions(
                transport=httpx2.ASGITransport(app=asgi_app) if asgi_app else httpx2.AsyncHTTPTransport(),
            ),
        )
