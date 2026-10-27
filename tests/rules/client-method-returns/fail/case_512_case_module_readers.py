# The same case with its readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_raw(self) -> httpx2.Response:
        return await self.get("x", expect=X)
