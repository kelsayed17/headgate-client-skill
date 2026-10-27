# The dominant shape (214 methods): a t-string path, the query collector, a decoder.
# Readers moved to module level (R3).
AGGS_ENVELOPE = decoder(AggsEnvelope)


class MassiveClient(AsyncBaseClient):
    async def get_aggs(self, ticker: str, **params: Unpack[AggsParams]) -> AggsEnvelope:
        """``GET /v2/aggs/ticker/{ticker}`` — the bars."""
        return await self.get(t"v2/aggs/ticker/{ticker}", params=params, expect=AGGS_ENVELOPE)
