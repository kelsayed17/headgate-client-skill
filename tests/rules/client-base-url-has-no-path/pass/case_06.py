_BARS_PATH = "v2/stocks/bars"
_HOST = "https://data.example.org"

class C(AsyncBaseClient):
    def __init__(self) -> None:
        T(base_url=_HOST, path=_BARS_PATH)
        T(url="https://h.example.org/x")
