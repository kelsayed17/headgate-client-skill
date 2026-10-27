class C(AsyncBaseClient):
    def __init__(self, host: str) -> None:
        super().__init__(base_url=f"https://{host}", rate=Rate.per_second(_MAX_RATE_PER_SEC))
