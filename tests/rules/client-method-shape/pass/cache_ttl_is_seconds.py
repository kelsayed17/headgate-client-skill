# cache_ttl= is seconds: an int or float literal, None, or a parameter.
class C(AsyncBaseClient):
    async def get_heating(self, year: int) -> Heating:
        return await self.get(t"heating/{year}", expect=decoder(Heating), cache_ttl=3600)

    async def get_cooling(self, year: int) -> Cooling:
        return await self.get(t"cooling/{year}", expect=decoder(Cooling), cache_ttl=0.5)
