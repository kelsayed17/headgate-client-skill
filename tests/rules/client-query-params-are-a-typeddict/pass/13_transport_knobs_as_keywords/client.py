class C(AsyncBaseClient):
    async def get_x(self, retry: bool = True, **params: Unpack[XParams]) -> X:
        return await self.get("x", params=params, expect=decoder(X), timeout=LONG_READ, retry=retry)
