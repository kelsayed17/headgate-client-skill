# A loop with an `else:` after the chunks.
class Grid(AsyncBaseClient):
    async def stream_x(self, year: int) -> AsyncIterator[bytes]:
        async with self.stream("x") as stream:
            async for chunk in stream.aiter_bytes():
                yield chunk
            else:
                yield _trailer
