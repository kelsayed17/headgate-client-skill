from headgate import AsyncBaseClient, Rate

RATE = Rate(5)
LIVE_URL = "https://api.broker.example"
PAPER_URL = "https://paper-api.broker.example"

SANDBOX_URL = "https://sandbox.broker.example"


class TradingClient(AsyncBaseClient):
    def __init__(self, *, live: bool, test: bool) -> None:
        super().__init__(base_url=LIVE_URL if live else (PAPER_URL if test else SANDBOX_URL), rate=RATE)
