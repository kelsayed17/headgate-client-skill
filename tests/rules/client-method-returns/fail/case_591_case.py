Maybe = A | None


class C(AsyncBaseClient):
    async def get_a(self) -> Maybe:
        return await self.get("a", expect=decoder(A))
