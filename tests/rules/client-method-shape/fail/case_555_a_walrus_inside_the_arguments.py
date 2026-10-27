# A walrus inside the arguments.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, s: str) -> X:
        return await self.get((path := t"x/{s}"), expect=X)
