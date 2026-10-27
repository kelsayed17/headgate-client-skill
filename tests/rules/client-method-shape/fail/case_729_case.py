# Readers moved to module level (R3).
A = decoder(A)


class C(AsyncBaseClient):
    async def get_a(self, **params: Unpack[P]) -> A:
        return await self.get("/a", params=params, params2=params, expect=A)
