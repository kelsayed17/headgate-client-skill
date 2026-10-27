# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def create(self, name: str) -> X:
        return await self.post("x", json=_body(name), expect=X)
