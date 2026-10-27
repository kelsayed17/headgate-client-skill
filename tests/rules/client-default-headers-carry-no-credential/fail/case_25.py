class C(AsyncBaseClient):
    def __init__(self, key: str) -> None:
        self._headers = {"X-Api-Key": key}
        super().__init__(http=HttpOptions(headers=self._headers))
