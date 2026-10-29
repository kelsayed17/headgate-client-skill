class C(AsyncBaseClient):
    def __init__(self, *, live: bool, test: bool) -> None:
        super().__init__(base_url=_LIVE_URL if live else (_PAPER_URL if test else _SANDBOX_URL), rate=Rate.per_second(_MAX_RATE_PER_SEC))
