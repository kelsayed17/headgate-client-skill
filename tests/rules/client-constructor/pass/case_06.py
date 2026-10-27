class _Base(AsyncBaseClient):
    def __init__(self, *, token: str) -> None:
        super().__init__(base_url=_BASE_URL, rate=Rate.per_second(_MAX_RATE_PER_SEC))


class Concrete(_Base):
    def __init__(self, *, token: str) -> None:
        super().__init__(token=token)
