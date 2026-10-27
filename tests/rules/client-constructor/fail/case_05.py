class C(AsyncBaseClient):
    def __init__(self, *args: Any) -> None:
        super().__init__(*args, base_url=_BASE_URL, rate=Rate.per_second(_MAX_RATE_PER_SEC))
