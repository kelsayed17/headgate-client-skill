# A loop that binds each chunk to an attribute, not a name of its own: the loop writes to the client.
class Grid(AsyncBaseClient):
    async def stream_x(self, year: int) -> AsyncIterator[bytes]:
        async with self.stream("x") as stream:
            async for self._chunk in stream.aiter_bytes():
                yield self._chunk
