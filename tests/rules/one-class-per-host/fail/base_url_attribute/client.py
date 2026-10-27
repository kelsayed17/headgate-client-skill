from headgate import AsyncBaseClient, Rate

RATE = Rate(5)


class Client(AsyncBaseClient):
    _BASE = "https://api.one.example"

    def __init__(self) -> None:
        super().__init__(base_url=self._BASE, rate=RATE)
