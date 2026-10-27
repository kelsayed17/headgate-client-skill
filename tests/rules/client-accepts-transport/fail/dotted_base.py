class FredClient(headgate.AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=_BASE_URL)
