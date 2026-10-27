# The same case with its readers moved to module level (R3).
STR_OBJECT = decoder(dict[str, object])


class C(AsyncBaseClient):
    async def get_x(self) -> dict[str, object]:
        return await self.get("x", expect=STR_OBJECT)
