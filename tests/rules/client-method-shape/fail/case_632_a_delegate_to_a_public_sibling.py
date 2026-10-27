# A delegate to a PUBLIC sibling, and to a leg on another object.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, s: str) -> X:
        return await self.get_y(s)

    async def get_y(self, s: str) -> X:
        return await self.get(t"y/{s}", expect=X)
