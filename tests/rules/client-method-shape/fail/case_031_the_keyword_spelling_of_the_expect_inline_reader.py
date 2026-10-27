# The keyword spelling of the Expect root is one argument too.
# R3: the source's inline reader; `expect=` is a module-level name here.
class C(AsyncBaseClient):
    async def get_x(self) -> X | NotFound:
        return await self.get("x", expect=Expect(ok=decoder(X)).on(404, decoder(NotFound)))
