class FredClient(AsyncBaseClient):
    def __init__(self, *, api_key: str) -> None:
        super().__init__(base_url=_BASE_URL, auth=QueryParamAuth({"api_key": api_key}), http=HttpOptions())
