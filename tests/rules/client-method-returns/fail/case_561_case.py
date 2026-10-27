class C(AsyncBaseClient):
    async def get_x(self) -> X | bytes:
        return await self.get("x", expect=Expect(decoder(X)).on(404, as_bytes))
