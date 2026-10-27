# The same case with its readers moved to module level (R3).
MUTABLE_MAPPING_STR_INT = decoder(MutableMapping[str, int])


class C(AsyncBaseClient):
    async def get_x(self) -> MutableMapping[str, int]:
        return await self.get("x", expect=MUTABLE_MAPPING_STR_INT)
