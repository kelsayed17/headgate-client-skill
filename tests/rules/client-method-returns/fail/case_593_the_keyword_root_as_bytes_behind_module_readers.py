# The keyword root: as_bytes behind a model; a keyword that is not ok=.
# The same case with its readers moved to module level (R3).
OK_AS_BYTES_404_NOT_FOUND = Expect(ok=as_bytes).on(404, decoder(NotFound))


class C(AsyncBaseClient):
    async def get_page(self) -> Page | NotFound:
        return await self.get("page", expect=OK_AS_BYTES_404_NOT_FOUND)
