# #1401's negative control: the marker FIRST reads decoded, so a fetch_ name is wrong.
class C(AsyncBaseClient):
    async def fetch_b(self) -> NotPublished | bytes:
        return await self.get("b", expect=Expect(as_bytes).on(404, decoder(NotPublished)))
