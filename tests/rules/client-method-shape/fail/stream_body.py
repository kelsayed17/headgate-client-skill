# A stream with a body: a stream is a GET here, its request what it was handed and nothing to send.
class Grid(AsyncBaseClient):
    async def stream_x(self, order: Order) -> AsyncIterator[bytes]:
        async with self.stream("x", body=NEW_ORDER(order)) as stream:
            async for chunk in stream.aiter_bytes():
                yield chunk
