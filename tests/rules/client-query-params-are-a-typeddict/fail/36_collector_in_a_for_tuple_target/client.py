class C(AsyncBaseClient):
    async def get_x(self, pairs: list[tuple[str, XParams]], **params: Unpack[XParams]) -> X:
        for _, params in pairs:
            return await self.get("x", params=params, expect=decoder(X))
