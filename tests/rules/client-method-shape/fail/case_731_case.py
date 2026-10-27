# Readers moved to module level (R3).
A = decoder(A)


class C(AsyncBaseClient):
    async def get_a(self, r: bool) -> A:
        return await self.post("/a", retry=not r, expect=A)
