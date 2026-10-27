# A shared non-headgate base beside AsyncBaseClient.
from headgate import AsyncBaseClient, Rate

WWW = "https://www.one.example"
DATA = "https://data.one.example"
RATE = Rate(5)


class _Helpers:
    def headers(self) -> dict[str, str]:
        return {}


class Www(AsyncBaseClient, _Helpers):
    def __init__(self) -> None:
        super().__init__(base_url=WWW, rate=RATE)


class Data(AsyncBaseClient, _Helpers):
    def __init__(self) -> None:
        super().__init__(base_url=DATA, rate=RATE)
