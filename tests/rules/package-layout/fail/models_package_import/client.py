from headgate import AsyncBaseClient, Rate

from . import models

API = "https://api.one.example"
RATE = Rate(5)


class Client(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=API, rate=RATE)

    async def get_item(self) -> models.Item:
        return await self.get("item", expect=models.Item)
