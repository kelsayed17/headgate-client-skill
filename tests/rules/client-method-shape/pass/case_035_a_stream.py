# A stream: headgate's unbuffered verb, its chunks handed on as they arrive.
class Grid(AsyncBaseClient):
    async def stream_balance(self, year: int, half: Half) -> AsyncIterator[bytes]:
        """``GET /balance``, streamed."""
        async with self.stream(t"files/BALANCE_{year}_{half}.csv") as stream:
            async for chunk in stream.aiter_bytes():
                yield chunk
