class Probe(httpx2.AsyncBaseTransport):
    def __init__(self, limiter) -> None:
        self._limiter = limiter

    async def handle_async_request(self, request):
        await self._limiter.acquire()
        return await super().handle_async_request(request)
