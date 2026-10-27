_LIVE = "https://api.example.org"
_PAPER = "https://paper-api.example.org"

class C(AsyncBaseClient):
    def __init__(self, live: bool) -> None:
        T(base_url=_LIVE if live else _PAPER)
        T(base_url=_LIVE if "x/y" else _PAPER)
