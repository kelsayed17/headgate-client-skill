# Comments inside Expect(...) and .on(...) are not arguments.
class C(AsyncBaseClient):
    async def get_page(self) -> Page | NotFound:
        return await self.get(
            "page",
            expect=Expect(
                # the success reader
                decoder(Page)
            ).on(
                # a documented answer
                404,
                decoder(NotFound),
            ),
        )
