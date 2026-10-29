# A loop over something other than the stream the `async with` opened.
class Grid(AsyncBaseClient):
    async def stream_x(self, year: int) -> AsyncIterator[bytes]:
        async with self.stream("x") as stream:
            async for chunk in _other.aiter_bytes():
                yield chunk
