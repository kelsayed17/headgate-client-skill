# #1401's documented-answer marker after the raw arm (`bytes | NotPublished`), which the source passed: a raw
# return, and a `fetch_` name.
# Its reader at module level.
AS_BYTES_404_NOT_PUBLISHED = Expect(as_bytes).on(404, decoder(NotPublished))


class C(AsyncBaseClient):
    async def fetch_a(self) -> bytes | NotPublished:
        return await self.get("a", expect=AS_BYTES_404_NOT_PUBLISHED)
