class C(AsyncBaseClient):
    async def get_x(self, **params: Unpack[XParams]) -> X:
        try:
            raise _Query()
        except _Query as params:
            return await self.get("x", params=params, expect=decoder(X))
