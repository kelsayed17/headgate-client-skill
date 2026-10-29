# A loop that yields something other than the chunk it read.
class Grid(AsyncBaseClient):
    async def stream_x(self, year: int) -> AsyncIterator[bytes]:
        async with self.stream("x") as stream:
            async for chunk in stream.aiter_bytes():
                yield _header
