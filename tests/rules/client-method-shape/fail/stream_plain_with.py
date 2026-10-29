# A stream opened with a plain `with`: headgate's stream is an async context manager.
class Grid(AsyncBaseClient):
    async def stream_x(self, year: int) -> AsyncIterator[bytes]:
        with self.stream("x") as stream:
            async for chunk in stream.aiter_bytes():
                yield chunk
