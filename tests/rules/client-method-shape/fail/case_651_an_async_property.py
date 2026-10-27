# An async property.
class C(AsyncBaseClient):
    @property
    async def total(self) -> int:
        return 1
