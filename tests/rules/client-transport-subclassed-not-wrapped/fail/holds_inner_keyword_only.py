class SlowTransport:
    def __init__(self, *, wrapped, delay: float = 0.0) -> None:
        self.wrapped = wrapped
        self.delay = delay

    async def handle_async_request(self, request):
        await sleep(self.delay)
        return await self.wrapped.handle_async_request(request)
