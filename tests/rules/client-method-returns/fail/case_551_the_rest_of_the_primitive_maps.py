# The rest of the primitive maps.
class C(AsyncBaseClient):
    async def get_x(self) -> Mapping[str, str]:
        return await self.get("x", expect=decoder(Mapping[str, str]))
