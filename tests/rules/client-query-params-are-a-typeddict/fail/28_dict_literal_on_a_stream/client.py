class C(AsyncBaseClient):
    async def stream_x(self, year: int) -> AsyncIterator[bytes]:
        async with self.stream("x", params={"year": year}) as stream:
            async for chunk in stream.aiter_bytes():
                yield chunk
