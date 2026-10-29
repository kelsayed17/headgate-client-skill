# A stream with the knobs a stream takes, a literal, a parameter or a module constant; a comment is not a statement.
class Fed(AsyncBaseClient):
    async def stream_z1(self, retry: bool = True) -> AsyncIterator[bytes]:
        async with self.stream("releases/z1.zip", retry=retry, timeout=LONG_READ, deadline=LONG_READ_DEADLINE) as s:
            # chunks, as they arrive
            async for c in s.aiter_bytes():
                yield c
