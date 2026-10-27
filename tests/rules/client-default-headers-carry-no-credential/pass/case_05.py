_AUTH = {"Authorization": "Bearer x"}
_HEADERS = {"Accept": "application/json"}


class C(AsyncBaseClient):
    _DEFAULTS = {"Accept": "text/csv"}

    def __init__(self) -> None:
        super().__init__(http=HttpOptions(headers=_HEADERS))
        super().__init__(http=HttpOptions(headers=self._DEFAULTS))
        super().__init__(http=HttpOptions(headers={**_HEADERS, "X-Trace": "1"}))
