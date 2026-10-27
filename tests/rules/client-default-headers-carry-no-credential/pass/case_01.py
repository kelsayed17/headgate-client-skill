class CftcClient(AsyncBaseClient):
    def __init__(self, user_agent: str, app_token: str) -> None:
        super().__init__(
            base_url=_BASE_URL,
            auth=StaticHeaderAuth({"X-App-Token": app_token}),
            http=HttpOptions(headers={"Accept": "application/json", "User-Agent": user_agent, "X-Trace": app_token}),
        )
