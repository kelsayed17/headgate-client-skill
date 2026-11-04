# The keyword spelling of the root, as the clients README documents it.
class C(AsyncBaseClient):
    async def get_x(self) -> X | NotFound:
        return await self.get("x", expect=Expect(ok=decoder(X)).on(404, decoder(NotFound)))
