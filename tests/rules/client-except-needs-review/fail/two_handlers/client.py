from headgate import AsyncBaseClient


class ItemClient(AsyncBaseClient):
    async def item(self, item_id: str) -> object | None:
        try:
            return await self.get(f"/items/{item_id}", expect=ITEM)
        except KeyError:
            return None
        except (ValueError, TypeError):
            return None
        finally:
            self.done = True
