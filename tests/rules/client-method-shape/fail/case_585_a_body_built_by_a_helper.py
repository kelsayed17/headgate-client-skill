# A body built by a helper, a function or a constructor (no Request/Params/Body suffix needed).
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def create(self, name: str) -> X:
        return await self.post("x", json=self._body(name), expect=X)
