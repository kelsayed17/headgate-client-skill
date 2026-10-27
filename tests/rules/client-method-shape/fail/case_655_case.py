# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def add(self, body=_DEFAULT) -> X:
        return await self.post("x", json=_DEFAULT, expect=X)
