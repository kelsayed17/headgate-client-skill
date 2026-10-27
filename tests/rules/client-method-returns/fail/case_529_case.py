class XGuestClient(AsyncBaseClient):
    async def get_graphql(self, query_id: str, **params: Unpack[GraphqlParams]) -> Any:
        return await self.get(t"graphql/{query_id}", params=params, expect=decoder(dict[str, Any]))
