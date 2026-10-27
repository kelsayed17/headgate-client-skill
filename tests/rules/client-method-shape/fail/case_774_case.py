# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def add(self, body: Body) -> X:
        return await self.post("x", body=_WRITE(self.body), expect=X)
