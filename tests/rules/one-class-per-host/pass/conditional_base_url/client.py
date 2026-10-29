from headgate import AsyncBaseClient, Rate, as_bytes

RATE = Rate(5)
LIVE_URL = "https://api.broker.example"
PAPER_URL = "https://paper-api.broker.example"


class TradingClient(AsyncBaseClient):
    def __init__(self, *, live: bool) -> None:
        super().__init__(base_url=LIVE_URL if live else PAPER_URL, rate=RATE)

    async def get_statement(self) -> bytes:
        return await self.get("https://paper-api.broker.example/statement", expect=as_bytes)
