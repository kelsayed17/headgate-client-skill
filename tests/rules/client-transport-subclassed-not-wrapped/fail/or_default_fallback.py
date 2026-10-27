class Fallback(httpx2.AsyncBaseTransport):
    def __init__(self, inner=None) -> None:
        self._inner = inner or httpx2.AsyncHTTPTransport()

    async def handle_async_request(self, request):
        return await self._inner.handle_async_request(request)
