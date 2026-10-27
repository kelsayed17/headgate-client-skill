_PROD_BASE = "https://api.tradier.com/v1"

class _TradierBase(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=self._BASE)

class TradierClient(_TradierBase):
    _BASE: ClassVar[str] = _PROD_BASE
