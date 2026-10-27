# #1401's negative control: the marker FIRST reads decoded, so a fetch_ name is wrong.
# The same case with its readers moved to module level (R3).
AS_BYTES_404_NOT_PUBLISHED = Expect(as_bytes).on(404, decoder(NotPublished))


class C(AsyncBaseClient):
    async def fetch_b(self) -> NotPublished | bytes:
        return await self.get("b", expect=AS_BYTES_404_NOT_PUBLISHED)
