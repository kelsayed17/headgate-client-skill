# Readers moved to module level (R3).
A = decoder(A)


class C(AsyncBaseClient):
    async def get_a(self) -> A:
        return await self.get("/a", follow_redirects=_FOLLOW, expect=A)
