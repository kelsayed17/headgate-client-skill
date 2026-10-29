# A stream bound to an attribute, not a name of its own: the with item writes to the client.
class Grid(AsyncBaseClient):
    async def stream_x(self, year: int) -> AsyncIterator[bytes]:
        async with self.stream("x") as self._open:
            async for chunk in self._open.aiter_bytes():
                yield chunk
