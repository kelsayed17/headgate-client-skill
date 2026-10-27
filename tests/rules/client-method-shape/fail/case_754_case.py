# Readers moved to module level (R3).
A = decoder(A)


class C(AsyncBaseClient):
    async def get_a(self, a: str, extra={1}) -> A:
        return await self.get(t"/a/{a}", expect=A)
