class C(AsyncBaseClient):
    _HEADERS = {"X-Token": "t"}

    def __init__(self) -> None:
        super().__init__(http=HttpOptions(headers=self._HEADERS))
