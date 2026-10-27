# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", headers=_JSON_HEADERS, expect=X)
