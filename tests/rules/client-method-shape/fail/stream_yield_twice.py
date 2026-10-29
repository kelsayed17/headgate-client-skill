# A loop that does something besides yielding the chunk.
class Grid(AsyncBaseClient):
    async def stream_x(self, year: int) -> AsyncIterator[bytes]:
        async with self.stream("x") as stream:
            async for chunk in stream.aiter_bytes():
                yield chunk
                yield chunk
