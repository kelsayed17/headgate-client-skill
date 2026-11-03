import msgspec
from headgate import AsyncBaseClient, Rate

API = "https://api.one.example"
RATE = Rate(5)


class Item(msgspec.Struct, frozen=True, gc=False):
    id: str


class Client(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=API, rate=RATE)
