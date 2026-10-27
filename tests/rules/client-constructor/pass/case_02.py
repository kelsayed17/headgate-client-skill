_MAX_RATE_PER_MIN = 120

class FredClient(AsyncBaseClient):
    def __init__(self, *, api_key: str) -> None:
        super().__init__(
            base_url=_BASE_URL,
            rate=Rate.per_minute(_MAX_RATE_PER_MIN),
            auth=QueryParamAuth({"api_key": api_key}),
        )
