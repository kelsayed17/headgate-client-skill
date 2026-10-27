# The query collector is `**params: Unpack[<X>Params]`, the endpoint's TypedDict.
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, **params: Unpack[XBody]) -> X:
        return await self.get("x", params=params, expect=X)
