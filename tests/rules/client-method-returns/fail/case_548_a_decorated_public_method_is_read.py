# A decorated public method is read.
class C(AsyncBaseClient):
    @traced
    async def get_x(self) -> Any:
        return await self.get("x", expect=decoder(X))
