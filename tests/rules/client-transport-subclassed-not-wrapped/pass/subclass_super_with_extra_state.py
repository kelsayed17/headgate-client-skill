class PacedTransport(httpx2.AsyncHTTPTransport):
    def __init__(self, limiter, **kwargs) -> None:
        super().__init__(**kwargs)
        self._limiter = limiter

    async def handle_async_request(self, request: httpx2.Request) -> httpx2.Response:
        await self._limiter.acquire()
        return await super().handle_async_request(request)
