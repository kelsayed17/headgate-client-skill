# The same case with its readers moved to module level (R3).
STR_BOOL = decoder(dict[str, bool])


class C(AsyncBaseClient):
    async def get_x(self) -> dict[str, bool]:
        return await self.get("x", expect=STR_BOOL)
