from headgate import AsyncBaseClient, Rate

RATE = Rate(5)


class Base(AsyncBaseClient):
    def __init__(self, base_url: str) -> None:
        super().__init__(base_url=base_url, rate=RATE)
