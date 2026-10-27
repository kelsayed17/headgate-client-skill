class C(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=_BASE_URL, max_rate=_MAX_RATE_PER_SEC)
