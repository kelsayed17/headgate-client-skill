class C(AsyncBaseClient):
    _BASE = "https://api.example.org/v1"

    def __init__(self) -> None:
        super().__init__(base_url=self._BASE)
