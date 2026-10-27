# Two private attributes naming the same constant are not a duplicate; an annotated default carrying a call in
# its TYPE is not a built default; comments inside Expect(...) and .on(...).
# Readers moved to module level (R3).
PAGE_OR_NOT_FOUND = Expect(
    # the success reader
    decoder(Page)
).on(
    # a documented answer
    404,
    decoder(NotFound),
)


class Hosts(AsyncBaseClient):
    _BASE: ClassVar[str] = _HOST
    _ALT: ClassVar[str] = _HOST

    async def get_page(self, limit: Annotated[int, Field(gt=0)] = 10) -> Page:
        return await self.get(
            "page",
            expect=PAGE_OR_NOT_FOUND,
        )
