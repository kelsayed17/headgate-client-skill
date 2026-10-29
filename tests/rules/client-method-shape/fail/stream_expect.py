# A stream with `expect=`, even a module reader: a 2xx is a stream's only success, so it takes no reader.
class Grid(AsyncBaseClient):
    async def stream_x(self, year: int) -> AsyncIterator[bytes]:
        async with self.stream("x", expect=X) as stream:
            async for chunk in stream.aiter_bytes():
                yield chunk
