# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def upload(self, blob: bytes) -> X:
        return await self.post("x", files={"file": blob}, expect=X)
