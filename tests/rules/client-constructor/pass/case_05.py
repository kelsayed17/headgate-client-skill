class _TradierBase(AsyncBaseClient):
    _BASE: ClassVar[str]

    def __init__(self, *, token: str) -> None:
        super().__init__(base_url=self._BASE, rate=Rate.per_minute(_MAX_RATE_PER_MIN))


class TradierClient(_TradierBase):
    _BASE: ClassVar[str] = _PROD_BASE


class _InternalClient(AsyncBaseClient):
    def __init__(self, *, base_url: str = "http://internal") -> None:
        super().__init__(
            base_url=base_url,
            rate=Rate.per_second(_MAX_RATE_PER_SEC),
            policy=TransportPolicy(retry=_RETRY, breaker=None),
        )
