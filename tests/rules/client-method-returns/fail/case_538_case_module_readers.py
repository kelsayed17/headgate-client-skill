# The same case with its readers moved to module level (R3).
STR_INT = decoder(dict[str, int])


class C(AsyncBaseClient):
    async def get_x(self) -> dict[str, int]:
        return await self.get("x", expect=STR_INT)
