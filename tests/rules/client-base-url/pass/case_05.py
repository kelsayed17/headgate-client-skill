class C(AsyncBaseClient):
    def __init__(self, *, live: bool) -> None:
        super().__init__(base_url=hosts.LIVE if live else hosts.PAPER, rate=Rate.per_second(_MAX_RATE_PER_SEC))
