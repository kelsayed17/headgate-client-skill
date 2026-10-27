# Model names that END in Response are models, not httpx2.Response.
class BlsClient(AsyncBaseClient):
    async def get_series_chunk(self, request: BlsSeriesRequest) -> BlsResponse:
        return await self.post("publicAPI/v2/timeseries/data/", json=to_builtins(request), expect=decoder(BlsResponse))

    async def get_quote(self, **params: Unpack[QuoteParams]) -> QuoteResponseEnvelope:
        return await self.get("v7/finance/quote", params=params, expect=decoder(QuoteResponseEnvelope))
