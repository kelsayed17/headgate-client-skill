# A stream read with a plain `for`: the chunks arrive through an async iterator.
class Grid(AsyncBaseClient):
    async def stream_x(self, year: int) -> AsyncIterator[bytes]:
        async with self.stream("x") as stream:
            for chunk in stream.aiter_bytes():
                yield chunk
