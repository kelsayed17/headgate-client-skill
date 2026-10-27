class C(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(Rate.per_second(_MAX_RATE_PER_SEC), base_url=_BASE_URL)
