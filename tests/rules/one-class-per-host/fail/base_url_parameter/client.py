# A base URL the caller picks is not a module-level name: the class no longer names its host.
from headgate import AsyncBaseClient, Rate

RATE = Rate(5)


class Client(AsyncBaseClient):
    def __init__(self, base_url: str) -> None:
        super().__init__(base_url=base_url, rate=RATE)
