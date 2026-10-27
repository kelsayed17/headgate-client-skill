# An as_bytes root with a model first; bytes then str; a chain on a void; Expect(nothing).
class C(AsyncBaseClient):
    async def get_page(self) -> Page | NotFound:
        return await self.get("page", expect=Expect(as_bytes).on(404, decoder(NotFound)))
