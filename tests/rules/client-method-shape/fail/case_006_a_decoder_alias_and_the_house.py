# A decoder alias and the house expect forms.
_EITS_BODY = decoder(list[list[str]], allow_empty_body=True)

class CensusClient(AsyncBaseClient):
    async def get_eits_marts(self, **params: Unpack[EitsParams]) -> CensusEitsResponse:
        return await self.get(t"{_EITS}/marts", expect=_EITS_BODY, params=params)
