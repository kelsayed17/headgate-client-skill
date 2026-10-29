from headgate import AsyncBaseClient, Rate

RATE = Rate(5)
LIVE_URL = "https://api.broker.example"
PAPER_URL = "https://paper-api.broker.example"


class TradingClient(AsyncBaseClient):
    def __init__(self, *, live: bool) -> None:
        super().__init__(base_url=LIVE_URL if live else "https://paper-api.broker.example", rate=RATE)
