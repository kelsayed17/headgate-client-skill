# The second host's URL constant is imported from a sibling module and passed to a verb.
from headgate import AsyncBaseClient, Rate

from .hosts import API, OTHER_URL

RATE = Rate(5)


class Client(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=API, rate=RATE)

    async def get_other(self) -> Other:
        return await self.get(OTHER_URL, expect=OTHER)
