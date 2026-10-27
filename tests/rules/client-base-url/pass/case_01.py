_BASE_URL = "https://api.stlouisfed.org"

class FredClient(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=_BASE_URL, rate=Rate.per_second(_MAX_RATE_PER_SEC))


class _TradierBase(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=self._BASE, rate=Rate.per_minute(_MAX_RATE_PER_MIN))
