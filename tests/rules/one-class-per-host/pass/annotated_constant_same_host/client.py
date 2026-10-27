# A Final-annotated base URL, and an absolute URL constant on the class's own host.
from typing import Final

from headgate import AsyncBaseClient, Rate

API: Final = "https://api.one.example"
EXPORT_URL = "https://api.one.example/v2/export"
RATE = Rate(5)


class Client(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=API, rate=RATE)

    async def get_export(self) -> Export:
        return await self.get(EXPORT_URL, expect=EXPORT)
