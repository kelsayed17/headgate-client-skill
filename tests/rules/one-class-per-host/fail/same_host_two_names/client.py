# Two names, one host: still two classes for one host.
from headgate import AsyncBaseClient, Rate

READS = "https://api.one.example"
WRITES = "https://API.one.example:443"
RATE = Rate(5)


class Reads(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=READS, rate=RATE)


class Writes(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=WRITES, rate=RATE)
