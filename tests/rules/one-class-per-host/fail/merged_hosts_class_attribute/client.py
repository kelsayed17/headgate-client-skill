# The second host held in a class attribute, passed as `self.<name>`.
from headgate import AsyncBaseClient, Rate

API = "https://api.one.example"
RATE = Rate(5)


class Client(AsyncBaseClient):
    _SERIES = "https://data.two.example/series"

    def __init__(self) -> None:
        super().__init__(base_url=API, rate=RATE)

    async def get_series(self) -> Series:
        return await self.get(self._SERIES, expect=SERIES)
