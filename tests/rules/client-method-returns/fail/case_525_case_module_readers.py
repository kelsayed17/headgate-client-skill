# The same case with its readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self) -> X | None:
        return await self.get("x", expect=X)
