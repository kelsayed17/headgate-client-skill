# `bytes`/`str` as a TYPE ARGUMENT are not a raw body: a stream's chunks, a decoded array of strings, a map of models
# keyed by string, a Literal. Model names that merely start with `Bytes`/`Str` are models.
class C(AsyncBaseClient):
    async def stream_exports(self) -> AsyncIterator[bytes]:
        async with self.stream("exports") as s:
            async for c in s.aiter_bytes():
                yield c

    async def get_symbols(self) -> list[str]:
        return await self.get("symbols", expect=decoder(list[str]))

    async def get_quotes(self) -> dict[str, Quote]:
        return await self.get("quotes", expect=decoder(dict[str, Quote]))

    async def get_kind(self) -> Literal["bytes", "str"]:
        return await self.get("kind", expect=decoder(Literal["bytes", "str"]))

    async def get_ranges(self) -> BytesPage | StrikePrice:
        return await self.get("ranges", expect=decoder(BytesPage | StrikePrice))
