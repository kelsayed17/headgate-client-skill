class C(AsyncBaseClient):
    async def get_x(self, **params: Unpack[XParams]) -> X:
        return await self.get("x", **params, **_DEFAULTS)
