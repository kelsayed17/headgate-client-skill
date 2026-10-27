# A splat of a global into a leg.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self._leg(**_DEFAULTS)

    async def _leg(self, **params: Unpack[P]) -> X:
        return await self.get("x", params=params, expect=X)
