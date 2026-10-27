class C(AsyncBaseClient):
    async def get_raw(self) -> Response:
        return await self.get("x", expect=decoder(X))
