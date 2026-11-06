# R3: every type-expression form of a plain reader at the call: a builtin, a generic, a union, a dotted model, a bare
# map, and pydantic's `adapter`.
class C(AsyncBaseClient):
    async def get_count(self) -> int:
        return await self.get("count", expect=decoder(int))

    async def get_rows(self) -> DataEnvelope[Row]:
        return await self.get("rows", expect=decoder(DataEnvelope[Row]))

    async def get_row_or_rows(self) -> list[Row] | Row:
        return await self.get("either", expect=decoder(list[Row] | Row))

    async def get_filing(self) -> models.Filing:
        return await self.get("filing", expect=decoder(models.Filing))

    async def get_by_id(self) -> dict[str, Row]:
        return await self.get("by-id", expect=decoder(dict[str, Row]))

    async def get_quote(self) -> Quote:
        return await self.get("quote", expect=adapter(Quote))
