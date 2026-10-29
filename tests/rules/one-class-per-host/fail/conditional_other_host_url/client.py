from headgate import AsyncBaseClient, Rate, as_bytes

RATE = Rate(5)
LIVE_URL = "https://api.broker.example"
PAPER_URL = "https://paper-api.broker.example"


class TradingClient(AsyncBaseClient):
    def __init__(self, *, live: bool) -> None:
        super().__init__(base_url=LIVE_URL if live else PAPER_URL, rate=RATE)

    async def get_other(self) -> bytes:
        return await self.get("https://data.broker.example/x", expect=as_bytes)
