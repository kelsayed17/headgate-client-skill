type Blob = dict[str, Any]


class C(AsyncBaseClient):
    async def get_a(self) -> Blob:
        return await self.get("a", expect=decoder(A))
