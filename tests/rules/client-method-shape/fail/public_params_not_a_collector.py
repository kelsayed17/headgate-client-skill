# Query parameters arrive as `**params: Unpack[<X>Params]`, not as one mapping argument.
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, params: XParams) -> X:
        return await self.get("x", params=params, expect=X)
