# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def add(self) -> X:
        return await self.post("x", body=_WRITE(_DEFAULT_BODY), expect=X)
