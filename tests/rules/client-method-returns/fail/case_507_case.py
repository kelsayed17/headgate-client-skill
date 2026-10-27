_RAW = as_bytes

class C(AsyncBaseClient):
    async def get_page(self) -> Page:
        return await self.get("page", expect=_RAW)
