# cache_ttl=False is a bool too: zero seconds by accident. Say `cache_ttl=0` or leave it out.
class C(AsyncBaseClient):
    async def get_heating(self, year: int) -> Heating:
        return await self.get(t"heating/{year}", expect=decoder(Heating), cache_ttl=False)
