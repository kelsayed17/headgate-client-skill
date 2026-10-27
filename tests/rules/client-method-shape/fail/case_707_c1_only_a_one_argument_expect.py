# C1: only a ONE-argument Expect root is not a request built from scalars.
class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", expect=Expect(decoder(X), accept="text/csv").on(404, decoder(NotFound)))
