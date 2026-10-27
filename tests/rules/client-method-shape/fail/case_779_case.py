# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def add(self, body: Body) -> X:
        return await self.post("x", json=to_builtins(body, drop_none=True), expect=X)
