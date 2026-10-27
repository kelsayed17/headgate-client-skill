class SecClient(AsyncBaseClient):
    def __init__(self, *, user_agent: str = DEFAULT_USER_AGENT) -> None:
        super().__init__(base_url=_BASE_URL, rate=_RATE)
