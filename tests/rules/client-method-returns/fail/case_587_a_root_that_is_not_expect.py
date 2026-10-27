# A root that is not Expect; an answer method that is not .on.
class C(AsyncBaseClient):
    async def get_x(self) -> X | NotFound:
        return await self.get("x", expect=Reader(decoder(X)).on(404, decoder(NotFound)))
