# The rest of the primitive maps.
# The same case with its readers moved to module level (R3).
MAPPING_STR_STR = decoder(Mapping[str, str])


class C(AsyncBaseClient):
    async def get_x(self) -> Mapping[str, str]:
        return await self.get("x", expect=MAPPING_STR_STR)
