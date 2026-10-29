# A stream opened without `as`: nothing names the stream the loop reads.
class Grid(AsyncBaseClient):
    async def stream_x(self, year: int) -> AsyncIterator[bytes]:
        async with self.stream("x"):
            async for chunk in _stream.aiter_bytes():
                yield chunk
