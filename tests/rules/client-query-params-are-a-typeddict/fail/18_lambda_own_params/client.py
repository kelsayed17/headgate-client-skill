class C(AsyncBaseClient):
    async def get_x(self, symbol: str, **params: Unpack[XParams]) -> X:
        send = lambda params: self.get("x", params=params, expect=decoder(X))
        return await send({"symbol": symbol})
