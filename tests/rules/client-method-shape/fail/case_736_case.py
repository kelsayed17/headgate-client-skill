# Readers moved to module level (R3).
A = decoder(A)


class C(AsyncBaseClient):
    async def get_a(self, params: P = {"limit": 100, "sort": "desc"}) -> A:
        return await self.get("/a", expect=A)
