_SANDBOX_BASE = "https://sandbox.tradier.com"
_PROD_BASE = "https://api.tradier.com"

class _TradierBase(AsyncBaseClient):
    _BASE: ClassVar[str]

    def __init__(self) -> None:
        super().__init__(base_url=self._BASE, rate=Rate.per_minute(_MAX_RATE_PER_MIN))

class TradierClient(_TradierBase):
    _BASE: ClassVar[str] = _PROD_BASE

class TradierSandboxClient(_TradierBase):
    _BASE: ClassVar[str] = _SANDBOX_BASE
