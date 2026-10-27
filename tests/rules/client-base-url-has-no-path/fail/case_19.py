_LIVE = "https://api.example.org/v2"
_PAPER = "https://paper-api.example.org"

class C(AsyncBaseClient):
    def __init__(self, live: bool) -> None:
        super().__init__(base_url=_LIVE if live else _PAPER)
