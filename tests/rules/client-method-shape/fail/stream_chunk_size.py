# A stream read in chunks of a size the method picks: `aiter_bytes()` takes no argument here.
class Grid(AsyncBaseClient):
    async def stream_x(self, year: int) -> AsyncIterator[bytes]:
        async with self.stream("x") as stream:
            async for chunk in stream.aiter_bytes(1024):
                yield chunk
