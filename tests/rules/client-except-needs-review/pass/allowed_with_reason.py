from headgate import AsyncBaseClient


class ItemClient(AsyncBaseClient):
    async def item(self, item_id: str) -> object | None:
        try:
            return await self.get(f"/items/{item_id}", expect=ITEM)
        except KeyError:  # headgate-verify: allow client-except-needs-review -- a missing item is the provider's documented answer
            return None
