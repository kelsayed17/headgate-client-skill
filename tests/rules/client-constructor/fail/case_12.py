_LIMITER = AsyncRateLimiter(10, 1)

class C(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=_BASE_URL, rate_limiter=_LIMITER)
