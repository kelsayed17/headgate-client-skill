class InternalHttpClient(AsyncBaseClient):
    def __init__(self, token: str) -> None:
        super().__init__(http=HttpOptions(headers={"Accept": "application/json", "X-Internal-Token": token}), rate=_RATE)
