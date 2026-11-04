# The dominant shape (214 methods): a t-string path, the query collector, a decoder.
# R3: the same shape with its reader written at the call, `expect=decoder(Type)`, which is a plain type reader.
class MassiveClient(AsyncBaseClient):
    async def get_aggs(self, ticker: str, **params: Unpack[AggsParams]) -> AggsEnvelope:
        """``GET /v2/aggs/ticker/{ticker}`` — the bars."""
        return await self.get(t"v2/aggs/ticker/{ticker}", params=params, expect=decoder(AggsEnvelope))
