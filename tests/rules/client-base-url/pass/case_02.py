class _InternalClient(AsyncBaseClient):
    def __init__(self, *, service_token: str, base_url: str = "http://internal") -> None:
        super().__init__(base_url=base_url, rate=Rate.per_second(_MAX_RATE_PER_SEC))
