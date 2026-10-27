# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, headers: dict[str, str]) -> X:
        return await self.get("x", headers=_HEADERS, expect=X)
