# The same case with its readers moved to module level (R3).
A = decoder(A)


Maybe = A | None


class C(AsyncBaseClient):
    async def get_a(self) -> Maybe:
        return await self.get("a", expect=A)
