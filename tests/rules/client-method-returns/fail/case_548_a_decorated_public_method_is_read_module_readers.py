# A decorated public method is read.
# The same case with its readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    @traced
    async def get_x(self) -> Any:
        return await self.get("x", expect=X)
