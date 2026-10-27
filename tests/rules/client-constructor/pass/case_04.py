class OpenFigiClient(AsyncBaseClient):
    def __init__(self, *, key: str | None = None) -> None:
        super().__init__(
            base_url=_BASE_URL,
            rate=Rate.per_minute(_MAX_RATE_KEYED_PER_MIN if key else _MAX_RATE_ANON_PER_MIN),
        )
