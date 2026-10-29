class C(AsyncBaseClient):
    async def get_x(self, symbol: str, **params: Unpack[XParams]) -> X:
        def inject() -> None:
            nonlocal params
            params = {"symbol": symbol}

        inject()
        return await self.get("x", params=params, expect=decoder(X))
