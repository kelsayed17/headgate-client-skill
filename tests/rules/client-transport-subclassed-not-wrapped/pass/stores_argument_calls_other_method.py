class RecordingTransport(httpx2.AsyncBaseTransport):
    def __init__(self, inner: httpx2.AsyncBaseTransport) -> None:
        self._inner = inner

    async def handle_async_request(self, request: httpx2.Request) -> httpx2.Response:
        return await super().handle_async_request(request)

    async def aclose(self) -> None:
        await self._inner.aclose()
