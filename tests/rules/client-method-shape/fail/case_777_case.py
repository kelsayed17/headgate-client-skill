# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def add(self, body: EncodedBody) -> X:
        return await self.post("x", body=body, expect=X)
