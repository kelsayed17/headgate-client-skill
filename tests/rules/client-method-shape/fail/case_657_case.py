# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def add(self, **params: Unpack[FormBody]) -> X:
        return await self.post("x", data=FormBody, expect=X)
