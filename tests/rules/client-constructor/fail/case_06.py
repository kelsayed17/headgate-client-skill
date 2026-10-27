class C(AsyncBaseClient):
    def __init__(self) -> None:
        super(C, self).__init__(base_url=_BASE_URL, rate=Rate.per_second(_MAX_RATE_PER_SEC))
