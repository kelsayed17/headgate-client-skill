# A bare Expect(as_bytes) behind a model.
# The same case with its readers moved to module level (R3).
AS_BYTES = Expect(as_bytes)


class C(AsyncBaseClient):
    async def get_page(self) -> Page:
        return await self.get("page", expect=AS_BYTES)
