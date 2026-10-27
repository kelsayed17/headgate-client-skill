# The same case with its readers moved to module level (R3).
STR_FLOAT = decoder(list[dict[str, float]])


class C(AsyncBaseClient):
    async def get_x(self) -> list[dict[str, float]]:
        return await self.get("x", expect=STR_FLOAT)
