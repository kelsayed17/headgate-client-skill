_ROWS = decoder(list[Row])


class C(AsyncBaseClient):
    async def get_rows(self) -> list[Row] | NotFound:
        return await self.get("rows", expect=Expect(ok=_ROWS).on(404, decoder(NotFound)))
