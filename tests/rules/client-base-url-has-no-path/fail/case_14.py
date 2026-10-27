_BASE_URL = _ALIAS = ("https://api.example.org/v1")

class C(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=_BASE_URL)
