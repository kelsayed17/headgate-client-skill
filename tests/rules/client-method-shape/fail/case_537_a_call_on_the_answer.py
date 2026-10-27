# A call on the answer.
# Readers moved to module level (R3).
ROW = decoder(list[Row])


class C(AsyncBaseClient):
    async def get_x(self) -> list[Row]:
        return sorted(await self.get("x", expect=ROW))
