# One class, two hosts: the second host's paths reach it as absolute URLs, a literal and a t-string.
from headgate import AsyncBaseClient, Rate

API = "https://api.one.example"
RATE = Rate(5)


class Client(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=API, rate=RATE)

    async def get_items(self) -> Items:
        return await self.get("items", expect=ITEMS)

    async def get_series(self) -> Series:
        return await self.get("https://data.two.example/series", expect=SERIES)

    async def get_series_item(self, series_id: str) -> Series:
        return await self.get(t"https://data.two.example/series/{series_id}", expect=SERIES)
