# asyncio.gather as the statement.
# Readers moved to module level (R3).
A = decoder(A)
B = decoder(B)


class C(AsyncBaseClient):
    async def get_both(self, **params: Unpack[P]) -> tuple[A, B]:
        return await asyncio.gather(self.get("a", expect=A), self.get("b", expect=B))
