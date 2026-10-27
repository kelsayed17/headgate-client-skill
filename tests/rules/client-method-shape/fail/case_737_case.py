# Readers moved to module level (R3).
A = decoder(A)


class C(AsyncBaseClient):
    async def get_a(self, u: str, f=lambda: 1) -> A:
        return await self.get("/a", expect=A)
