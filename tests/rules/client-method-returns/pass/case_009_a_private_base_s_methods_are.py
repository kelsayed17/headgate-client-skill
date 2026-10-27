# A private base's methods are checked like any other; these conform.
class _TradierBase(AsyncBaseClient):
    async def get_quotes(self, **params: Unpack[QuotesParams]) -> QuotesResponse:
        return await self.get("v1/markets/quotes", params=params, expect=decoder(QuotesResponse))


class TradierClient(_TradierBase):
    _BASE: ClassVar[str] = _PROD_BASE
