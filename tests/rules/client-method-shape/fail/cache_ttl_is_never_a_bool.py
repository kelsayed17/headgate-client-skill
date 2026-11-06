# cache_ttl= is seconds (`float | None`); a bool is an int, so `cache_ttl=True` caches for one second.
class C(AsyncBaseClient):
    async def get_heating(self, year: int) -> Heating:
        return await self.get(t"heating/{year}", expect=decoder(Heating), cache_ttl=True)
