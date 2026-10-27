class Aliased(httpx2.AsyncBaseTransport):
    def __init__(self, inner) -> None:
        self._inner = inner

    async def handle_async_request(self, request):
        inner = self._inner
        return await inner.handle_async_request(request)
