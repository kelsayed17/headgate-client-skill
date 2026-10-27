class C(AsyncBaseClient):
    _BASE = _HOST
    _OTHER = "https://h.example.org/v1"

    def __init__(self) -> None:
        super().__init__(base_url=self._BASE)
        T(base_url=hosts._OTHER)

_HOST = "https://h.example.org"
