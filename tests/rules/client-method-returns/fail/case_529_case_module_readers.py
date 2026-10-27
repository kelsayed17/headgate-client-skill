# The same case with its readers moved to module level (R3).
STR_ANY = decoder(dict[str, Any])


class XGuestClient(AsyncBaseClient):
    async def get_graphql(self, query_id: str, **params: Unpack[GraphqlParams]) -> Any:
        return await self.get(t"graphql/{query_id}", params=params, expect=STR_ANY)
