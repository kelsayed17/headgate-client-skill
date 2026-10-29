from headgate import AsyncBaseClient, Rate

RATE = Rate(5)
LIVE_URL = "https://api.broker.example"
PAPER_URL = "https://paper-api.broker.example"


class TradingClient(AsyncBaseClient):
    def __init__(self, *, live: bool) -> None:
        super().__init__(
            base_url=LIVE_URL  # the live host
            if live
            else PAPER_URL,  # the paper host
            rate=RATE,
        )
