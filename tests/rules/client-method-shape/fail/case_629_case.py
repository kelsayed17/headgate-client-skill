# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self) -> X:
        """Two requests."""
        await self.post("warm", expect=nothing)
        return await self.get("x", expect=X)
