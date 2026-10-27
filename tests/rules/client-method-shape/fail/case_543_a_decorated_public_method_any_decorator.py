# A decorated public method (any decorator but @property).
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    @traced
    async def get_x(self) -> X:
        return await self.get("x", expect=X)
