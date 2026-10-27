class Probe(httpx2.AsyncBaseTransport):
    def __init__(self, inner) -> None:
        self._inner = inner
        self._seen = None

    async def handle_async_request(self, request):
        self._seen = request
        return await self._seen.handle_async_request(request)
