class SecClient(AsyncBaseClient):
    def __init__(self, *, user_agent: str) -> None:
        super().__init__(base_url=_BASE_URL, rate=_RATE, http=HttpOptions(headers={"User-Agent": user_agent}))


def bare(user_agent) -> None:
    pass


async def build(api_key: str, user_agent: str, *, timeout: float = 30.0) -> None:
    pass
