# A decoder alias bound at module level, including an annotated binding.
_EITS_BODY = decoder(list[list[str]], allow_empty_body=True)
_ROWS: Final = decoder(list[Row])

class CensusClient(AsyncBaseClient):
    async def get_eits_marts(self, **params: Unpack[EitsParams]) -> CensusEitsResponse:
        return await self.get(t"{_EITS}/marts", expect=_EITS_BODY, params=params)

    async def get_rows(self) -> list[Row]:
        return await self.get("rows", expect=_ROWS)
