from .models import Items

from headgate import AsyncBaseClient, Rate

API = "https://api.one.example"
RATE = Rate(5)


class Client(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=API, rate=RATE)

    async def get_items(self) -> Items:
        return await self.get("items", expect=ITEMS)
