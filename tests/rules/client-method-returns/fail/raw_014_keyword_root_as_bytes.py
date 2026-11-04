# The keyword spelling of an `as_bytes` root is a raw return like the positional one.
class C(AsyncBaseClient):
    async def get_y(self) -> bytes | NotFound:
        return await self.get("y", expect=Expect(ok=as_bytes).on(404, decoder(NotFound)))
