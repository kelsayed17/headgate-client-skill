# The keyword root: as_bytes behind a model; a keyword that is not ok=.
class C(AsyncBaseClient):
    async def get_page(self) -> Page | NotFound:
        return await self.get("page", expect=Expect(ok=as_bytes).on(404, decoder(NotFound)))
