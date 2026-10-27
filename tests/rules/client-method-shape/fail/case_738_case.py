# Readers moved to module level (R3).
A = decoder(A)


class C(AsyncBaseClient):
    async def get_a(self, params: dict = _DEFAULTS) -> A:
        return await self.get("/a", params=params, expect=A)
