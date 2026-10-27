class FredClient(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=_BASE_URL, http=HttpOptions(transport=transport))

    def rebuild(self, transport: Transport) -> None:
        pass
