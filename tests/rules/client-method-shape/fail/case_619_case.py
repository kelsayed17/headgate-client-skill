# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient, Mixin):
    async def get_x(self) -> X:
        return await self.get("x", expect=X)
