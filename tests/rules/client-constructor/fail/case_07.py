class C(AsyncBaseClient):
    def __init__(self) -> None:
        AsyncBaseClient.__init__(self, base_url=_BASE_URL, rate=Rate.per_second(_MAX_RATE_PER_SEC))
