# A private base defined in this file, and concrete subclasses carrying only a private ClassVar.
# R3: the source's inline reader; `expect=` is a module-level name here.
class _TradierBase(AsyncBaseClient):
    """The endpoint surface."""

    _BASE: ClassVar[str]

    def __init__(self, *, token: str) -> None:
        super().__init__(base_url=self._BASE, rate=Rate.per_minute(_MAX_RATE_PER_MIN))

    async def get_quotes(self, **params: Unpack[QuotesParams]) -> QuotesResponse:
        return await self.get("v1/markets/quotes", params=params, expect=decoder(QuotesResponse))


class TradierClient(_TradierBase):
    """``api.tradier.com``."""

    _BASE: ClassVar[str] = _PROD_BASE


class TradierSandboxClient(_TradierBase):
    _BASE: ClassVar[str] = _SANDBOX_BASE
    pass
