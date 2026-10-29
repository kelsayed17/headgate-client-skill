# A stream item in one pair of parentheses, with the query and headers it was handed.
class Grid(AsyncBaseClient):
    async def stream_x(self, headers: Headers, **params: Unpack[XParams]) -> AsyncIterator[bytes]:
        async with (self.stream("x", params=params, headers=headers, follow_redirects=False) as stream):
            async for chunk in stream.aiter_bytes():
                yield chunk
