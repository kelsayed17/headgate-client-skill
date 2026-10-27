# An as_bytes root with a model first; bytes then str; a chain on a void; Expect(nothing).
# The same case with its readers moved to module level (R3).
AS_BYTES_404_NOT_FOUND = Expect(as_bytes).on(404, decoder(NotFound))


class C(AsyncBaseClient):
    async def get_page(self) -> Page | NotFound:
        return await self.get("page", expect=AS_BYTES_404_NOT_FOUND)
