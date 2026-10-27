# An await inside the arguments.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, **params: Unpack[P]) -> X:
        return await self.get("x", params=params, headers=await self._headers(), expect=X)
