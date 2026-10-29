# A stream block that does something after the loop.
class Grid(AsyncBaseClient):
    async def stream_x(self, year: int) -> AsyncIterator[bytes]:
        async with self.stream("x") as stream:
            async for chunk in stream.aiter_bytes():
                yield chunk
            yield _trailer
