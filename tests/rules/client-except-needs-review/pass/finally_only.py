from headgate import AsyncBaseClient


class ItemClient(AsyncBaseClient):
    async def item(self, item_id: str) -> object:
        try:
            return await self.get(f"/items/{item_id}", expect=ITEM)
        finally:
            self.done = True
