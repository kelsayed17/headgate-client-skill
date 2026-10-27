class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", expect=Expect(decoder(Foo(1))))
