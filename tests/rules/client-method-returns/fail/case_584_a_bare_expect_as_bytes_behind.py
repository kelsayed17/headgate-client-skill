# A bare Expect(as_bytes) behind a model.
class C(AsyncBaseClient):
    async def get_page(self) -> Page:
        return await self.get("page", expect=Expect(as_bytes))
