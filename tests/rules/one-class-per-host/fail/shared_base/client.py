# Two hosts, but both classes share a private client base: the hosts' configuration is merged in one class.
from headgate import AsyncBaseClient, Rate

WWW = "https://www.one.example"
DATA = "https://data.one.example"
RATE = Rate(5)


class _Base(AsyncBaseClient):
    def __init__(self, base_url: str) -> None:
        super().__init__(base_url=base_url, rate=RATE)


class Www(_Base):
    def __init__(self) -> None:
        super().__init__(WWW)


class Data(_Base):
    def __init__(self) -> None:
        super().__init__(DATA)
