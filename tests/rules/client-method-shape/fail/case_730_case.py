# Readers moved to module level (R3).
A = decoder(A)


class C(AsyncBaseClient):
    async def get_a(self, k: str) -> A:
        return await self.get("/a", timeout=_budget(k), expect=A)
