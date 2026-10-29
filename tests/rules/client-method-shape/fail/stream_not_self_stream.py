# An `async with` around something other than headgate's `self.stream(...)`.
class Grid(AsyncBaseClient):
    async def stream_x(self, year: int) -> AsyncIterator[bytes]:
        async with self.open("x") as stream:
            async for chunk in stream.aiter_bytes():
                yield chunk
