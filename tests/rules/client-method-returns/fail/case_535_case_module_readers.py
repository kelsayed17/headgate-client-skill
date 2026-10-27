# The same case with its readers moved to module level (R3).
MAPPING_STR_ANY = decoder(Mapping[str, Any])


class C(AsyncBaseClient):
    async def get_x(self) -> Mapping[str, Any]:
        return await self.get("x", expect=MAPPING_STR_ANY)
