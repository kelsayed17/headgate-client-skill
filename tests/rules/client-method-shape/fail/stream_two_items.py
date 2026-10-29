# A stream opened beside another context manager in the same `async with`.
class Grid(AsyncBaseClient):
    async def stream_x(self, year: int) -> AsyncIterator[bytes]:
        async with self.stream("x") as stream, _lock:
            async for chunk in stream.aiter_bytes():
                yield chunk
