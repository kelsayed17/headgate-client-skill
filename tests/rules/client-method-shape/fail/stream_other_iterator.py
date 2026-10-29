# A stream read through some other iterator than `aiter_bytes()`: the chunks are handed on as they arrive.
class Grid(AsyncBaseClient):
    async def stream_x(self, year: int) -> AsyncIterator[bytes]:
        async with self.stream("x") as stream:
            async for chunk in stream.aiter_text():
                yield chunk
