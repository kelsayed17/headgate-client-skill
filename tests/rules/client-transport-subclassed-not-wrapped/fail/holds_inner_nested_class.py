def build():
    class Wrapped(httpx2.AsyncBaseTransport):
        def __init__(self, inner) -> None:
            self._inner = inner

        async def handle_async_request(self, request):
            return await self._inner.handle_async_request(request)

    return Wrapped
