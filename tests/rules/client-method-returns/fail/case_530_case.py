class C(AsyncBaseClient):
    async def get_x(self) -> typing.Any:
        return await self.get("x", expect=decoder(X))
