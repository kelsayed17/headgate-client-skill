# The same case with its readers moved to module level (R3).
STR_ANY = decoder(dict[str, Any])


class C(AsyncBaseClient):
    async def get_a(self) -> A:
        return await self.get("a", expect=STR_ANY)
