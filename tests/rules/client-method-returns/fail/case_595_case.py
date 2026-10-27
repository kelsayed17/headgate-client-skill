class C(AsyncBaseClient):
    async def get_x(self) -> X | NotFound:
        return await self.get("x", expect=Expect(ok=nothing).on(404, decoder(NotFound)))
