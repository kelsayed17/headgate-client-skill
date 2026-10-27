# A fan-out over a collection; a counter that is not the builtin; loops that await something other than a fetch:
# a lock, a sleep, a module function, a non-verb method, `self` itself, a gather over un-awaited fetches.
class CensusClient(AsyncBaseClient):
    async def get_years(self, years: list[int]) -> list[Body]:
        out = []
        for year in years:
            out.append(await self.get(t"x/{year}", expect=as_bytes))
        for _ in builtins.range(3):
            await self.get("/x")
        while True:
            await self._lock.acquire()
            await asyncio.sleep(1)
            await fetch_page()
            await self.get_quote("SPY")
            await self()
            await asyncio.gather(*(self.get(p) for p in pages))
            break
        return out
