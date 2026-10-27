from headgate import AsyncBaseClient
from headgate.errors import ClientError


class ItemClient(AsyncBaseClient):
    async def item(self, item_id: str) -> object:
        try:
            return await self.get(f"/items/{item_id}", expect=ITEM)
        except KeyError as exc:
            raise ClientError(str(exc)) from exc
