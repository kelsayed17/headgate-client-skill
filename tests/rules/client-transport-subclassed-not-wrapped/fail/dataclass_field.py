@dataclass
class Wrapped(httpx2.AsyncBaseTransport):
    inner: httpx2.AsyncBaseTransport

    async def handle_async_request(self, request):
        return await self.inner.handle_async_request(request)
