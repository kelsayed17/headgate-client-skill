# Every built default kind, on a parameter nothing forwards; a forwarded untyped default that is not None.
# Readers moved to module level (R3).
A = decoder(A)


class C(AsyncBaseClient):
    async def get_a(self, a: str, extra=[1]) -> A:
        return await self.get(t"/a/{a}", expect=A)
