class FredClient(AsyncBaseClient):
    def __init__(self, *, transport: Transport | None = None) -> None:
        super().__init__(base_url=_BASE_URL)
