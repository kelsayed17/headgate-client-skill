async def get_bars(self, symbol: str) -> Bars:
    return await self.get(t"/v2/stocks/{symbol}/bars", expect=decoder(Bars))

async def get_clock(self) -> Clock:
    return await self.get("/v2/clock", expect=decoder(Clock))

async def follow(self, page: Page) -> Page:
    url = page.next_url
    return await self.get(url, expect=decoder(Page))
