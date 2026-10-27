class RobinhoodOAuthClient(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=_OAUTH_BASE, rate=Rate.per_minute(10))
