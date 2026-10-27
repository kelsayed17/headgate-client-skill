# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def add(self) -> X:
        return await self.post("x", json=_BODY, expect=X)
