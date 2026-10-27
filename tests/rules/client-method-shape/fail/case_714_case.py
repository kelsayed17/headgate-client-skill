# Readers moved to module level (R3).
A = decoder(A)


class _Mixin:
    async def get_total(self, a: str) -> int:
        x = await self.get(t"/a/{a}", expect=A)
        return x.n


class C(_Mixin, AsyncBaseClient):
    async def get_a(self, a: str) -> A:
        return await self.get(t"/a/{a}", expect=A)
