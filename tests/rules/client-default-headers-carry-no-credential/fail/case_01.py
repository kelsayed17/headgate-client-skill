class CftcClient(AsyncBaseClient):
    def __init__(self, app_token: str) -> None:
        super().__init__(base_url=_BASE_URL, http=HttpOptions(headers={"X-App-Token": app_token}))
