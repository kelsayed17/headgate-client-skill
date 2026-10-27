# The same case with its readers moved to module level (R3).
STR_BYTES = decoder(dict[str, bytes])


class C(AsyncBaseClient):
    async def get_x(self) -> dict[str, bytes]:
        return await self.get("x", expect=STR_BYTES)
