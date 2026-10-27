# Two classes passing the same base URL name: two classes for one host.
from headgate import AsyncBaseClient, Rate

API = "https://api.one.example"
RATE = Rate(5)


class Reads(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=API, rate=RATE)


class Writes(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=API, rate=RATE)
