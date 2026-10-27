# The same case with its readers moved to module level (R3).
READER = decoder(list[dict])


class C(AsyncBaseClient):
    async def get_x(self) -> list[dict]:
        return await self.get("x", expect=READER)
