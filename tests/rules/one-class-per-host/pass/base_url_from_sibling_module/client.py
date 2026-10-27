# Base URL names imported from a sibling module are module-level names too; their hosts are read there.
from headgate import AsyncBaseClient, Rate

from .hosts import DATA, WWW

RATE = Rate(5)


class Www(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=WWW, rate=RATE)

    async def get_index(self) -> Index:
        return await self.get("https://www.filings.example/index.json", expect=INDEX)


class Data(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=DATA, rate=RATE)
