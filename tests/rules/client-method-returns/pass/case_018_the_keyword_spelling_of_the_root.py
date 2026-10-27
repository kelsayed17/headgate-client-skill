# The keyword spelling of the root, as the clients README documents it.
class C(AsyncBaseClient):
    async def get_x(self) -> X | NotFound:
        return await self.get("x", expect=Expect(ok=decoder(X)).on(404, decoder(NotFound)))

    async def fetch_y(self) -> bytes | NotFound:
        return await self.get("y", expect=Expect(ok=as_bytes).on(404, decoder(NotFound)))
