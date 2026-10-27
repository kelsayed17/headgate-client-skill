# The same case with its readers moved to module level (R3).
X = decoder(X)


@final
class C(AsyncBaseClient):
    async def get_x(self) -> Any:
        return await self.get("x", expect=X)
