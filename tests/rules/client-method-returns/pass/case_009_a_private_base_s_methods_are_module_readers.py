# A private base's methods are checked like any other; these conform.
# The same case with its readers moved to module level (R3).
QUOTES_RESPONSE = decoder(QuotesResponse)


class _TradierBase(AsyncBaseClient):
    async def get_quotes(self, **params: Unpack[QuotesParams]) -> QuotesResponse:
        return await self.get("v1/markets/quotes", params=params, expect=QUOTES_RESPONSE)


class TradierClient(_TradierBase):
    _BASE: ClassVar[str] = _PROD_BASE
