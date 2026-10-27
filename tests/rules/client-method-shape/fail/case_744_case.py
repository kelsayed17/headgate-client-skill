# Readers moved to module level (R3).
A = decoder(A)


class C(AsyncBaseClient):
    async def _leg(self, path: str) -> A:
        return await self.get(path, expect=A)

    async def get_a(self) -> A:
        return await self._leg("/a")

    _leg = _EVIL
