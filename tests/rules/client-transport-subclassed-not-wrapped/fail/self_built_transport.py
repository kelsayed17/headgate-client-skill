class Owns(httpx2.AsyncBaseTransport):
    def __init__(self) -> None:
        self._inner = httpx2.AsyncHTTPTransport()

    async def handle_async_request(self, request):
        return await self._inner.handle_async_request(request)
