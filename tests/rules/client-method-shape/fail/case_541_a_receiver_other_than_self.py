# A receiver other than self.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self._http.get("x", expect=X)
