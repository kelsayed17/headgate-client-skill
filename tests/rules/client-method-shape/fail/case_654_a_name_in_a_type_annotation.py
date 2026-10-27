# A name in a type annotation or a default value is not a parameter.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def add(self, body: Body) -> X:
        return await self.post("x", json=Body, expect=X)
