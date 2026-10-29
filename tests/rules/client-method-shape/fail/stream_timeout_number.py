# A stream whose `timeout=` is a number: the forward checks hold on a stream as on a verb.
class Grid(AsyncBaseClient):
    async def stream_x(self, year: int) -> AsyncIterator[bytes]:
        async with self.stream("x", timeout=30.0) as stream:
            async for chunk in stream.aiter_bytes():
                yield chunk
