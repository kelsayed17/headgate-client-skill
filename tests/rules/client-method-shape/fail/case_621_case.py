# Readers moved to module level (R3).
X = decoder(X)


@endpoints("x", "y")
class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", expect=X)
