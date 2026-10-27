class _Base(AsyncBaseClient):
    def __init__(self, *, token: str, timeout: float = 30.0) -> None:
        super().__init__(base_url=_BASE_URL, rate=Rate.per_second(_MAX_RATE_PER_SEC), http=HttpOptions(timeout=timeout))


class Concrete(_Base):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
