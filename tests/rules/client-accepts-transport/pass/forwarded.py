class FredClient(AsyncBaseClient):
    def __init__(self, *, api_key: str, transport: httpx2.AsyncBaseTransport | None = None) -> None:
        super().__init__(
            base_url=_BASE_URL,
            rate=Rate.per_second(2),
            auth=QueryParamAuth({"api_key": api_key}),
            http=HttpOptions(transport=transport),
        )
