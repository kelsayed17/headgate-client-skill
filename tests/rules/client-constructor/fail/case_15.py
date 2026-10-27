class C(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=_BASE_URL)
        self._pacer = Pacer(rate=Rate.per_second(_MAX_RATE_PER_SEC))
