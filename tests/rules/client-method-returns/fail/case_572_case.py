class C(AsyncBaseClient):
    async def get_x(self) -> X | NotFound:
        return await self.get("x", expect=headgate.Expect(decoder(X)).on(404, decoder(NotFound)))
