class C(AsyncBaseClient):
    async def get_x(self, symbol: str, **params: Unpack[XParams]) -> X:
        async def inner(params: dict[str, str]) -> X:
            return await self.get("x", params=params, expect=decoder(X))

        return await inner({"symbol": symbol})
