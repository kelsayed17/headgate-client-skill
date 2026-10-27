# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, *args: str) -> X:
        return await self.get(*args, expect=X)
